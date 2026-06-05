import gemmi

# Residue types to exclude from ligand detection
_STANDARD_AA = {
    "ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE",
    "LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL",
    "SEC","PYL","UNK",
}
_STANDARD_NUC = {"DA","DC","DG","DT","DI","A","C","G","U","I"}
_SOLVENT = {
    "HOH","WAT","DOD","SO4","EDO","GOL","PEG","ACT","MPD",
    "PO4","CLR","DMS","FMT","TRS","IOD","BME","EPE"
}


def get_resolution(path: str) -> dict:
    """Return the resolution of the structure in Angstroms."""
    st = gemmi.read_structure(path)

    res = st.resolution if st.resolution and st.resolution > 0 else None

    # Fallback: read directly from CIF tags
    if res is None:
        try:
            block = gemmi.cif.read(path).sole_block()
            for tag in ["_refine.ls_d_res_high",
                        "_reflns.d_resolution_high",
                        "_em_3d_reconstruction.resolution"]:
                val = block.find_value(tag)
                if val and val not in {"?", "."}:
                    res = float(val)
                    break
        except Exception:
            pass

    # Get experimental method
    method = "unknown"
    try:
        block = gemmi.cif.read(path).sole_block()
        m = block.find_value("_exptl.method")
        if m and m not in {"?", "."}:
            method = m.strip().strip("'\"")
    except Exception:
        pass

    return {"resolution": res, "unit": "Å" if res else None, "method": method}


def get_chains(path: str) -> dict:
    """Return the number and details of chains in the structure."""
    st = gemmi.read_structure(path)
    chains = []
    seen = set()

    for model in st:
        for chain in model:
            if chain.name in seen:
                continue
            seen.add(chain.name)
            polymer = chain.get_polymer()
            ptype = str(polymer.check_polymer_type()) if len(polymer) > 0 else "non-polymer"
            residue_count = sum(1 for _ in chain)
            chains.append({"id": chain.name, "type": ptype, "residue_count": residue_count})

    return {"chain_count": len(chains), "chains": chains}


def get_ligands(path: str) -> dict:
    """Return all ligands found in the structure."""
    st = gemmi.read_structure(path)
    found = []
    seen = set()

    for model in st:
        for chain in model:
            for res in chain:
                if res.entity_type not in (gemmi.EntityType.NonPolymer,
                                           gemmi.EntityType.Unknown):
                    continue
                name = res.name.strip()
                if name in _STANDARD_AA or name in _STANDARD_NUC or name in _SOLVENT:
                    continue
                key = f"{name}:{chain.name}:{res.seqid}"
                if key in seen:
                    continue
                seen.add(key)
                found.append({"id": name, "chain": chain.name, "seq_num": str(res.seqid)})

    # Fallback: read _pdbx_entity_nonpoly from CIF
    if not found:
        try:
            block = gemmi.cif.read(path).sole_block()
            table = block.find("_pdbx_entity_nonpoly.", ["name", "comp_id"])
            for row in table:
                comp = row[1].strip().strip("'\"")
                if comp in _SOLVENT or comp in _STANDARD_AA:
                    continue
                if comp in seen:
                    continue
                seen.add(comp)
                found.append({"id": comp, "chain": "?", "seq_num": "?", "name": row[0].strip().strip("'\"")} )
        except Exception:
            pass

    return {"ligand_count": len(found), "has_ligand": len(found) > 0, "ligands": found}


def get_missing_residues(path: str) -> dict:
    """Return residues present in the sequence but missing from ATOM records."""
    st = gemmi.read_structure(path)
    missing = []

    # Method A: compare full entity sequence vs observed ATOM residues
    for model in st:
        for chain in model:
            polymer = chain.get_polymer()
            if len(polymer) == 0:
                continue
            observed = {str(r.label_seq) for r in polymer if r.label_seq is not None}
            entity_id = next((r.entity_id for r in polymer), None)
            if entity_id is None:
                continue
            entity = st.get_entity(entity_id)
            if entity is None:
                continue
            for idx, mon in enumerate(entity.full_sequence, start=1):
                if str(idx) not in observed:
                    missing.append({"chain": chain.name, "seq_num": idx, "residue": mon})

    # Method B: read _pdbx_unobs_or_zero_occ_residues from CIF (more reliable)
    cif_missing = []
    try:
        block = gemmi.cif.read(path).sole_block()
        table = block.find("_pdbx_unobs_or_zero_occ_residues.",
                           ["auth_asym_id", "auth_comp_id", "auth_seq_id",
                            "PDB_model_num", "polymer_flag"])
        for row in table:
            if row[4].strip() != "Y":
                continue
            cif_missing.append({"chain": row[0].strip(), "residue": row[1].strip(),
                                 "seq_num": row[2].strip(), "model": row[3].strip()})
    except Exception:
        pass

    final = cif_missing if cif_missing else missing
    return {"missing_count": len(final), "missing_residues": final}
