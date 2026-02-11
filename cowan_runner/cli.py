from pathlib import Path
import shutil
import subprocess
import re

# -----------------------------
# Utilities for subshell logic
# -----------------------------
def normalize_cfg_label(cfg):
    """
    Normalize Cowan configuration labels:
    3d7, 3D7, 3D,7 → 3D7
    """
    cfg = cfg.replace(",", "").replace(" ", "")
    return cfg.upper()
def subshell_capacity(nl):
    """
    nl = '2p', '3d', '4f', '5g', ...
    capacity = 2(2l+1)
    """
    l_map = {"s": 0, "p": 1, "d": 2, "f": 3, "g": 4, "h": 5, "i": 6}
    l_letter = nl[-1].lower()
    if l_letter not in l_map:
        raise ValueError(f"Unsupported subshell: {nl}")
    l = l_map[l_letter]
    return 2 * (2*l + 1)


def term_label_from_subshell(subshell, occ):
    """
    Pure Cowan-safe label (PRINT ONLY):
    3d,7  -> 3D7
    4f,10 -> 4F10
    """
    n_part = subshell[:-1]
    l_part = subshell[-1].upper()
    return f"{n_part}{l_part}{occ}"


# -----------------------------
#  parser 
# -----------------------------


def parse_out36_FG(out36_path, valence_shell, hole_shell=None):



    RYD_TO_EV = 13.605693

    valence_shell = valence_shell.upper()
    hole_shell = hole_shell.upper() if hole_shell else None

    def shells_in_cfg(cfg):
        """
        Extract shells present in configuration.
        DOES NOT check occupancy.
        """
        return set(re.findall(r'\d+[SPDFGH]', cfg.upper()))

    def suffix(a, b):
        """
        Always return ordered suffix:
        df not fd
        pd not dp
        """
        order = "SPDFGHI"

        la, lb = a[-1], b[-1]

        if la == lb:
            return (la + lb).lower()

        return (
            la + lb if order.index(la) < order.index(lb)
            else lb + la
        ).lower()

    lines = Path(out36_path).read_text(errors="ignore").splitlines()

    cfg_re = re.compile(r"^\s*\d*\s*(.+?)\s+NCONF\s*=", re.I)

    zeta_header = re.compile(r"ZETA", re.I)
    slater_header = re.compile(r"SLATER INTEGRALS", re.I)

    zeta_line = re.compile(
        r"^\s*(\d+[SPDFGH])\s+\d+\.\s+"
        r"([0-9.+-Ee]+)\s+[0-9.+-Ee]+\s+"
        r"([0-9.+-Ee]+)",
        re.I
    )

    slater_line = re.compile(
        r"\(\s*(\d+[SPDFGH])\s*,\s*(\d+[SPDFGH])\s*\)\s+"
        r"(\d+)\s+([0-9.+-Ee]+)\s+RYD.*?"
        r"(\d+)\s+([0-9.+-Ee]+)\s+RYD",
        re.I
    )

    results = {}
    cfg_shells = {}

    current_cfg = None
    in_zeta = False

    for line in lines:

        # ---------------- CONFIG ----------------
        m = cfg_re.search(line)
        if m:
            current_cfg = m.group(1).strip()

            results.setdefault(current_cfg, {})
            cfg_shells[current_cfg] = shells_in_cfg(current_cfg)

            in_zeta = False
            continue

        if current_cfg is None:
            continue

        cfg = results[current_cfg]
        shells = cfg_shells[current_cfg]

        # ---------------- ZETA ----------------
        if zeta_header.search(line):
            in_zeta = True
            continue

        if in_zeta and slater_header.search(line):
            in_zeta = False
            continue

        if in_zeta:
            m = zeta_line.search(line)
            if not m:
                continue

            nl, bw, rvi = m.groups()
            nl = nl.upper()

            # ⭐ Only keep zeta for shells present
            if nl not in shells:
                continue

            bw = float(bw)
            rvi = float(rvi)

            zeta = bw if abs(bw) > 1e-8 else rvi

            cfg[f"zeta_{nl.lower()}"] = zeta * RYD_TO_EV
            continue

        # ---------------- SLATER ----------------
        m = slater_line.search(line)
        if not m:
            continue

        s1, s2, fk_k, fk_val, gk_k, gk_val = m.groups()

        s1 = s1.upper()
        s2 = s2.upper()

        fk_k = int(fk_k)
        gk_k = int(gk_k)

        fk = float(fk_val) * RYD_TO_EV
        gk = float(gk_val) * RYD_TO_EV

        # ======================================
        # SAME SHELL → ALWAYS KEEP (ff, dd)
        # ======================================
        if s1 == valence_shell and s2 == valence_shell:

            if fk_k in (2, 4, 6):
                cfg[f"F{fk_k}"] = fk

            if gk_k > 0 and abs(gk) > 1e-12:
                cfg[f"G{gk_k}{suffix(s1,s2)}"] = gk

            continue

        # ======================================
        # CROSS SHELL → ONLY if hole exists
        # ======================================
        if (
            hole_shell
            and {s1, s2} == {hole_shell, valence_shell}
            and hole_shell in shells
        ):

            suf = suffix(s1, s2)

            if fk_k in (2, 4, 6):
                cfg[f"F{fk_k}{suf}"] = fk

            if gk_k > 0 and abs(gk) > 1e-12:
                cfg[f"G{gk_k}{suf}"] = gk

    return results



def attach_out36_FG(params, out36_data):

    normalized = {
        normalize_cfg_label(k): v
        for k, v in out36_data.items()
    }

    for cfg_key in params:

        norm = normalize_cfg_label(cfg_key)

        for fk_cfg in normalized:

            if fk_cfg in norm:
                params[cfg_key].update(normalized[fk_cfg])
                break
# -----------------------------
# Run Cowan
# -----------------------------

def run_cowan(run_dir, subshell, hole_shell):

    shell_label = subshell.upper()   


    for cmd in ["rcn", "rcn2"]:
        print(f"\nExecuting: {cmd}")
        result = subprocess.run(cmd, cwd=run_dir, shell=True)
        if result.returncode != 0:
            print(f"Error running {cmd}")
            return

    # -----------------------------
    # read outputs
    # -----------------------------



    params = parse_out36_FG(
    run_dir / "OUT36",
    subshell,
    hole_shell
    )

    # Existing print (unchanged)
    for cfg, values in params.items():
        print(f"\n--- {cfg} ---")
        for k, v in values.items():
            print(f"{k:12} = {v:.4f} eV")

    print("\nCowan run finished successfully.")


# -----------------------------
# Create run + IN36
# -----------------------------

def create_cowan_run():

    base_dir = Path.cwd()
    runs_dir = base_dir / "runs"
    work_dir = base_dir / "WORK"
    runs_dir.mkdir(exist_ok=True)

    Z = input("Atomic number (Z): ").strip()
    element = input("Element symbol (e.g. Co, Ni, Ce,...): ").strip()
    ion = input("Ionization (e.g. 3+): ").strip()

    subshell = input("Open subshell (e.g. 3d,4d,4f): ").strip()
    hole_shell = input("Shell to create a hole (e.g. 2p,3d): ").strip()
    n = int(input("Occupation number n (e.g. 7 for 3d7): ").strip())

    print("\nSelect Cowan control mesh:")
    print(" 90  = non-relativistic")
    print("190 = relativistic (standard)")
    print("290 = relativistic (recommended for heavy atoms / f systems)")

    mesh_choice = input("Mesh [290 default]: ").strip() 

    if mesh_choice == "":
        mesh = "00290"
    elif mesh_choice in {"90", "190", "290"}:
        mesh = mesh_choice.zfill(5)   # -> 00090 / 00190 / 00290
    else:
        raise ValueError("Mesh must be 90, 190, or 290.")

    ion_number = int(ion.replace("+", "")) + 1
    ion_label = f"{ion_number}{element}{ion}"

    open_config = f"{subshell}{n}"
    excited_config = f"{subshell}{n+1}"

    term_ground = term_label_from_subshell(subshell, n)
    term_excited = term_label_from_subshell(subshell, n+1)

    cap = subshell_capacity(hole_shell)
    hole_full = f"{hole_shell}{cap}"
    hole_occ = f"{hole_shell}{cap-1}"

    run_dir = runs_dir / f"{element}_{ion}"
    run_dir.mkdir(exist_ok=True)

    control = (
    f"210 9    2   10  0.2    5.E-08    1.E-11-2   "
    f"{mesh[-3:]}   1.0  0.65  0.0 0.0    -6"
    )

    line1 = f"{int(Z):5d}    {ion_label:<6} {open_config:<16}  {hole_full}  {term_ground}"
    line2 = f"{int(Z):5d}    {ion_label:<6} {hole_occ} {excited_config:<11}  {hole_occ}  {term_excited}"


    with open(run_dir / "IN36", "w") as f:
        f.write(control + "\n")
        f.write(line1 + "\n")
        f.write(line2 + "\n")
        f.write("   -1\n")

    in2_text = (
    "G5INP     000 0.0000          00                "
    "339999999999 0.00     07209\n"
    "        -1\n"
    )

    with open(run_dir / "IN2", "w") as f:
        f.write(in2_text)

    run_cowan(run_dir, subshell,hole_shell)


# -----------------------------
# Run
# -----------------------------

if __name__ == "__main__":
    create_cowan_run()
