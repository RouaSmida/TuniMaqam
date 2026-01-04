import json
from models.maqam import Maqam


def normalize_note(note):
    """Normalize note to standard form (e.g., 'C', 'D', 'E-HALF-FLAT')"""
    if not note:
        return ""
    return ''.join([c for c in str(note).upper() if c.isalpha() or c in ['#', 'B', '-']]).strip()


def analyze_notes_core(notes, optional_mood=None):
    """
    Core maqam analysis algorithm using first-jins pattern matching.
    
    The algorithm compares input notes against the first jins (lower tetrachord/pentachord)
    of each maqam, which contains the tonic and characteristic intervals that define
    the maqam's identity.
    """
    input_notes = {normalize_note(n) for n in notes if n}
    if not input_notes:
        return []
    
    candidates = []
    
    for m in Maqam.query.all():
        ajnas = json.loads(m.ajnas_json) if m.ajnas_json else []
        
        # ============ FIRST JINS ONLY ============
        # Musically, the first jins (lower tetrachord/pentachord) is the primary
        # identifier of a maqam. It contains the tonic (qarar) and the characteristic
        # intervals that define the maqam's identity.
        
        first_jins_notes = set()
        if ajnas:
            first_jins = ajnas[0]  # Take only the first jins
            jins_notes = first_jins.get("notes", {})
            if isinstance(jins_notes, dict):
                en_notes = jins_notes.get("en", [])
                for n in en_notes:
                    first_jins_notes.add(normalize_note(n))
            elif isinstance(jins_notes, list):
                for n in jins_notes:
                    first_jins_notes.add(normalize_note(n))
        
        if not first_jins_notes:
            continue
        
        common = input_notes & first_jins_notes
        if not common:
            continue
        
        # ============ CONFIDENCE SCORING ALGORITHM ============
        num_input = len(input_notes)
        num_maqam = len(first_jins_notes)
        num_matched = len(common)
        
        # Precision: what fraction of user's notes are in this maqam (0-1)
        precision = num_matched / num_input
        
        # Coverage: what fraction of maqam's notes user provided (0-1)
        coverage = num_matched / num_maqam
        
        # Weighted combination: precision matters more
        base_score = (precision * 0.7) + (coverage * 0.3)
        
        # Match count multiplier: reward having more matching notes
        match_multipliers = {1: 0.5, 2: 0.7, 3: 0.85, 4: 0.95}
        match_mult = match_multipliers.get(num_matched, 1.0)
        
        # Apply multiplier
        confidence = base_score * match_mult
        
        # Small bonus for emotional alignment
        evidence = ["note_pattern_match"]
        if optional_mood and m.emotion and optional_mood.lower() in m.emotion.lower():
            confidence = min(1.0, confidence + 0.08)
            evidence.append("emotion_alignment")
        
        # Clamp to 0-1 and round to 2 decimal places
        confidence = round(max(0, min(1.0, confidence)), 2)

        candidates.append({
            "maqam": m.name_en,
            "maqam_ar": m.name_ar,
            "confidence": confidence,
            "reason": f"Matched {num_matched}/{num_input} input notes; {num_matched}/{num_maqam} maqam notes covered",
            "evidence": evidence,
            "matched_notes": list(common)
        })
    
    candidates.sort(key=lambda c: c["confidence"], reverse=True)
    return candidates[:5]  # Return top 5
