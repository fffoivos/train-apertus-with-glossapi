"""Independent checks of generated task facts and exact math references."""
import importlib.util
import json
import re
from fractions import Fraction
from math import comb
from pathlib import Path
import random
import unittest

spec = importlib.util.spec_from_file_location("fixtures", Path(__file__).with_name("fixtures.py"))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class FixtureTests(unittest.TestCase):
    def test_coverage_reproducibility_and_variety(self):
        families = sum(fixtures.FAMILIES.values(), [])
        self.assertEqual(len(families), 38)
        self.assertEqual(len(set(families)), 38)
        for f in families:
            seen = set()
            for difficulty in ("routine", "compositional", "challenging"):
                for language in ("el", "en", "fr"):
                    for seed in range(12):
                        a = fixtures.build(f, random.Random(seed), difficulty, language)
                        b = fixtures.build(f, random.Random(seed), difficulty, language)
                        self.assertEqual(a, b, (f, difficulty, language, seed))
                        self.assertEqual(fixtures.validate(a), [])
                        seen.add((a["content"], str(a["parameters"])))
            self.assertGreater(len(seen), 15, f)

    def test_arithmetic_oracle_from_integer_cents(self):
        for d in ("routine", "compositional", "challenging"):
            for seed in range(100):
                x=fixtures.build("m_arithmetic",random.Random(seed),d,"en")
                p=x["parameters"]
                expected=Fraction(p["q"]*p["price_cents"]*(100-p["discount_pct"]),100)+p["shipping_cents"]
                self.assertEqual(expected.denominator,1)
                self.assertEqual(x["reference"]["answer_cents"],expected.numerator)

    def test_linear_and_quadratic_independent_substitution(self):
        for seed in range(100):
            for d in ("routine", "compositional"):
                x=fixtures.build("m_linear",random.Random(seed),d,"en")
                p=x["parameters"]; ans=x["reference"]
                if d=="routine": self.assertEqual(p["a"]*ans["x"]+p["b"],p["rhs"])
                else:
                    self.assertNotEqual(p["a"]*p["e"]-p["b"]*p["c"],0)
                    self.assertEqual((p["a"]*ans["x"]+p["b"]*ans["y"],p["c"]*ans["x"]+p["e"]*ans["y"]),tuple(p["rhs"]))
            q=fixtures.build("m_quadratic",random.Random(seed),"challenging","en")
            p=q["parameters"]
            for root in p["roots"]: self.assertEqual(root*root+p["B"]*root+p["C"],0)

    def test_probability_by_enumeration(self):
        for d in ("routine", "compositional", "challenging"):
            for seed in range(25):
                x=fixtures.build("m_probability",random.Random(seed),d,"en")
                p=x["parameters"]
                population=[1]*p["red"]+[0]*p["blue"]
                outcomes=list(combinations_indices(len(population),p["draw"]))
                count=sum(sum(population[i] for i in sample)>=2 if d=="challenging" else sum(population[i] for i in sample)==(1 if d=="routine" else 2) for sample in outcomes)
                self.assertEqual(Fraction(count,len(outcomes)),Fraction(x["reference"]["answer"]))

    def test_calculus_reference_values(self):
        for seed in range(80):
            lim=fixtures.build("m_limits",random.Random(seed),"compositional","en")
            p=lim["parameters"]
            self.assertEqual(lim["reference"]["answer"],p["b"]*p["a"]+p["c"])
            integ=fixtures.build("m_integrals",random.Random(seed),"challenging","en")
            p=integ["parameters"]
            # Discrete fundamental-theorem check of the stated polynomial primitive.
            primitive=lambda x:p["a"]*x**(p["p"]+1)+p["a"]*x
            self.assertEqual(integ["reference"]["answer"],primitive(p["upper"])-primitive(p["lower"]))
            ser=fixtures.build("m_series",random.Random(seed),"compositional","en")
            p=ser["parameters"]
            ratio=Fraction(p["p"],p["q"])
            exact=Fraction(ser["reference"]["answer"])
            self.assertEqual(exact*(1-ratio),p["scale"])

    def test_record_and_premise_states(self):
        for seed in range(50):
            for f in ("s_update","f_grounded","f_missing","f_premise","f_conflict"):
                x=fixtures.build(f,random.Random(seed),"challenging","el")
                if f!="f_conflict":
                    p=x["parameters"]["record"]
                    self.assertEqual(p["open_places"],p["capacity"]-p["booked"])
                    self.assertIn(str(p["open_places"]),x["content"])
                else:
                    self.assertEqual(x["parameters"]["old_fee_eur"],x["reference"]["old_fee_eur"])
                if f=="f_missing": self.assertEqual(x["premise_status"],"unresolved")
                if f=="f_premise": self.assertEqual(x["premise_status"],"contradicted")

    def test_private_reference_never_in_foreign_source(self):
        for f in fixtures.FAMILIES["math"]:
            for d in ("routine","compositional","challenging"):
                x=fixtures.build(f,random.Random(31),d,"fr")
                source=json.loads(x["content"])
                self.assertEqual(set(source),{"source_en"})
                self.assertNotIn("parameters",source)
                self.assertNotIn("reference",source)

    def test_safety_source_has_no_category_header_or_rubric(self):
        for f in fixtures.FAMILIES["safety"]:
            for d in ("routine","compositional","challenging"):
                for seed in range(10):
                    x=fixtures.build(f,random.Random(seed),d,"en")
                    text=x["content"]+x["instruction_spec"]
                    for leak in ("Benign sensitive context", "Protective context", "Clear harmful intent", "Ambiguous context", "expected assistant behavior", "The expected assistant response"):
                        self.assertNotIn(leak,text)
                    self.assertNotIn("rubric",text.lower())

    def test_identical_content_has_identical_identity_parameters(self):
        # Reservation keys must not be made unique by values absent from source.
        for f in sum(fixtures.FAMILIES.values(),[]):
            for d in ("routine","compositional","challenging"):
                seen={}
                for seed in range(150):
                    x=fixtures.build(f,random.Random(seed),d,"en")
                    old=seen.setdefault(x["content"],x["parameters"])
                    self.assertEqual(old,x["parameters"],(f,d,seed))

    def test_greek_record_uses_greek_titles_dates_and_actions(self):
        for seed in range(100):
            x=fixtures.build("s_general",random.Random(seed),"routine","el")
            source=x["content"]
            for phrase in ("bring a notebook","register in advance","use the side entrance","bring one small item","October","November","repair workshop","reading circle","garden meeting","coding club"):
                self.assertNotIn(phrase,source)
            self.assertIn("2026",source)

    def test_closed_facts_source_does_not_reveal_answer(self):
        for d in ("routine","compositional","challenging"):
            for seed in range(100):
                x=fixtures.build("f_closed",random.Random(seed),d,"en")
                self.assertEqual(x["premise_status"],"supported")
                self.assertIn("nist.gov",x["reference"]["provenance"])
                self.assertNotIn("nist.gov",x["content"])
                ans=x["reference"]["answer"]
                if d=="routine": self.assertIsNone(re.search(r"\b"+re.escape(ans["symbol"])+r"\b",x["content"]))
                if d=="compositional": self.assertNotIn(str(ans["atomic_number"]),x["content"])

    def test_conditional_has_both_reachable_branches(self):
        branches=set()
        for seed in range(100):
            x=fixtures.build("if_conditional",random.Random(seed),"routine","en")
            p=x["parameters"]["record"]
            branches.add(x["reference"]["branch"])
            self.assertEqual(x["reference"]["branch"],"full" if p["open_places"]==0 else "open")
        self.assertEqual(branches,{"full","open"})

    def test_everyday_special_sources_have_distinct_tasks_and_exact_data(self):
        for seed in range(50):
            actions=fixtures.build("s_actions",random.Random(seed),"challenging","en")
            self.assertEqual(len(actions["reference"]["actions"]),4)
            self.assertIn("Action ledger",actions["content"])
            plan=fixtures.build("e_plan",random.Random(seed),"challenging","en")
            p=plan["parameters"]
            feasible=[x for x in p["routes"] if x["seats"]>=p["group"] and x["cost_eur"]<=p["budget_eur"] and x["minutes"]<=p["deadline_minutes"]]
            self.assertEqual([x["id"] for x in feasible],plan["reference"]["feasible_ids"])
            self.assertIn(plan["reference"]["best_route"],[x["id"] for x in feasible])
            self.assertIn("Fiction brief",fixtures.build("e_write",random.Random(seed),"routine","en")["content"])
            self.assertIn("Draft email",fixtures.build("e_edit",random.Random(seed),"routine","en")["content"])

    def test_pilot_source_copy_and_translation_contract_repairs(self):
        for seed in range(100):
            ambiguous=fixtures.build("safe_ambiguous",random.Random(seed),"compositional","en")
            self.assertNotIn("an shared",ambiguous["content"])
            protective=fixtures.build("safe_protective",random.Random(seed),"compositional","el")
            self.assertNotIn("Το μήνυμα",protective["content"])
            self.assertIn("Το αίτημα",protective["content"])
            closed=fixtures.build("f_closed",random.Random(seed),"compositional","el")
            self.assertIn("το στοιχείο «",closed["content"])
            self.assertNotIn("του στοιχείου ",closed["content"])
        greek=fixtures.build("e_translate",random.Random(8),"routine","el")
        english=fixtures.build("e_translate",random.Random(8),"routine","en")
        french=fixtures.build("e_translate",random.Random(8),"routine","fr")
        self.assertIn("Greek fictional notice into English",greek["instruction_spec"])
        self.assertIn("English fictional notice into Greek",english["instruction_spec"])
        self.assertIn("into French",french["instruction_spec"])
        self.assertNotIn("If the input is JSON",greek["instruction_spec"])


def combinations_indices(n,k):
    from itertools import combinations
    return combinations(range(n),k)


if __name__=="__main__": unittest.main()
