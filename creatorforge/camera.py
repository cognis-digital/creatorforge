"""Camera & shot generation — multi-cam coverage and the moves that feel cinematic.

Great footage isn't one locked-off angle; it's *coverage* — several cameras and
deliberate moves cut together. This module generates, for each beat, a shot list
with camera assignments (A/B/C/detail/drone/POV) and motivated camera moves
(dolly, push-in, crane, gimbal track, drone reveal, dolly-zoom, orbit, …),
chosen to match the style and to spike engagement where it matters (cold opens,
turns, climaxes get the showy moves).

It's a shot plan a DP could shoot, or a prompt set for a text-to-video model.
"""

from __future__ import annotations

from typing import List

CAMERA_MOVES = {
    "dolly_in": "slow dolly in — intensify",
    "dolly_out": "dolly out — reveal / isolate",
    "push_in": "subtle push-in on the emphasis word",
    "crane_up": "crane up — scale and grandeur",
    "jib_down": "jib down into the scene",
    "gimbal_track": "gimbal tracking alongside the subject",
    "drone_reveal": "drone pull-back — big reveal",
    "whip_pan": "whip pan — kinetic transition",
    "rack_focus": "rack focus — shift attention",
    "dolly_zoom": "dolly zoom (vertigo) — unease / awe",
    "orbit": "orbit around the subject",
    "handheld": "handheld — energy and immediacy",
    "locked_off": "locked-off static — let it breathe",
    "top_down": "top-down overhead — clean layout",
    "snorricam": "subject-locked snorricam — disorienting",
    "speed_ramp": "speed ramp — hit the beat",
}

CAMERAS = {
    "A": "A-cam · eye-level medium (the anchor)",
    "B": "B-cam · tight close-up / reactions",
    "C": "C-cam · wide establishing / safety",
    "D": "D-cam · macro detail insert",
    "drone": "aerial",
    "POV": "POV / action cam",
}

# signature 'cool shot' moves to reach for at each beat role
_SIGNATURE = {
    "cold_open": ["drone_reveal", "crane_up", "dolly_zoom"],
    "hook": ["push_in", "whip_pan", "speed_ramp"],
    "thesis": ["push_in", "locked_off"],
    "rising_action": ["gimbal_track", "dolly_in"],
    "build": ["gimbal_track", "handheld", "speed_ramp"],
    "turn": ["dolly_zoom", "rack_focus", "whip_pan"],
    "climax": ["orbit", "dolly_zoom", "drone_reveal"],
    "breakthrough": ["crane_up", "push_in"],
    "demo": ["top_down", "rack_focus"],
    "proof": ["push_in", "top_down"],
    "resolution": ["dolly_out", "locked_off"],
    "conclusion": ["dolly_out", "crane_up"],
    "outro": ["drone_reveal", "dolly_out"],
    "cta": ["push_in"],
}

_FRAMINGS = ["extreme wide", "wide", "medium", "medium close-up", "close-up", "extreme close-up", "insert"]


def coverage(beat: str, purpose: str, topic: str, style: dict, n_shots: int = 3) -> List[dict]:
    """Generate a multi-cam shot list for one beat."""
    moves = _SIGNATURE.get(beat, ["push_in", "locked_off", "gimbal_track"])
    style_moves = [m for m in style.get("shot_vocab", []) ]
    cam_cycle = ["A", "B", "C", "D"]
    shots: List[dict] = []
    for i in range(max(1, n_shots)):
        move_key = moves[i % len(moves)]
        cam = "drone" if move_key in ("drone_reveal", "crane_up") and i == 0 else cam_cycle[i % len(cam_cycle)]
        framing = _FRAMINGS[(i + (0 if cam == "A" else 2)) % len(_FRAMINGS)]
        shots.append({
            "cam": cam,
            "cam_role": CAMERAS[cam],
            "framing": framing,
            "move": move_key,
            "move_note": CAMERA_MOVES[move_key],
            "description": f"{framing} of {topic} — {purpose}; {CAMERA_MOVES[move_key]}",
        })
    return shots


def multicam_plan(scenes: List[dict]) -> dict:
    """Summarize which cameras a whole production needs and the cool-shot count."""
    cams = set()
    cool = 0
    for s in scenes:
        for shot in s.get("shots", s.get("coverage", [])):
            cams.add(shot["cam"])
            if shot["move"] in ("dolly_zoom", "drone_reveal", "orbit", "crane_up", "speed_ramp"):
                cool += 1
    return {"cameras_needed": sorted(cams), "camera_legend": {c: CAMERAS[c] for c in sorted(cams)},
            "signature_shots": cool}
