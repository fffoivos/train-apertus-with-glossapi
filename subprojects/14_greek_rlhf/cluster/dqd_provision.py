import os, sys, types, argparse
sys.path.insert(0, '/Users/foivoskarounos-zamparloukos/Projects/greek-page-ocr/scripts')
os.environ['PRIME_INTELLECT_CONTROL_KEY'] = open(os.path.expanduser('~/.config/prime/key')).read().strip()
os.environ['GREEK_SWEEP_GPU_WHITELIST'] = 'A100_40GB'
os.environ['PRIME_MAX_PRICE_HR'] = '2.5'
os.environ['PRIME_MAX_HOURS'] = '2'
os.environ['GREEK_SWEEP_POD_STATE'] = sys.argv[1]
os.environ['GREEK_SWEEP_IMAGE'] = 'ubuntu_22_cuda_12'
import prime_provision as P
P.POD_NAME = 'greek-rlhf-dialogue'

_real = P.get_availability
def filtered():
    d = _real()
    out = {}
    for o in d.get('A100_40GB', []):
        if o.get('gpuCount') == 1 and o.get('security') == 'secure_cloud':
            o.setdefault('gpuType', 'A100_40GB')
            out.setdefault('A100_40GB', []).append(o)
    print(f'filtered availability: {len(out.get("A100_40GB", []))} single-GPU A100_40GB offer(s)')
    return out
P.get_availability = filtered

args = argparse.Namespace(image='ubuntu_22_cuda_12', disk_gb=100, network_volume=None,
                          timeout=1500, poll_interval=15, force=False)
sys.exit(P.cmd_provision(args))
