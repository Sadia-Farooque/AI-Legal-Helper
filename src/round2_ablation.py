"""Round 2 data ablation on the J1 test set: what does each change add? (same LR setting, no new grid search)

A baseline (original data, original normaliser) -> B + chat-spelling normaliser -> C + Roman Urdu chat stories
-> D + Supreme Court of Pakistan facts -> E all. Writes results/round2_ablation.csv.
The final configuration was chosen on VALIDATION (E >= C on every validation subset), not on this test table.

Run:  python -m src.round2_ablation
"""
import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd, numpy as np
import src.preprocess as pp
from src.models.classical import fit, label_names, load_dataset
from src.models.tfidf_lr import _best_params
NEW_KEYS = [k for k in list(pp.ROMAN_URDU_MAP)[list(pp.ROMAN_URDU_MAP).index("kl"):]]
FULL = dict(pp.ROMAN_URDU_MAP); OLD = {k: v for k, v in FULL.items() if k not in NEW_KEYS}
rows, labels, params = load_dataset(), label_names(), _best_params()
train = [r for r in rows if r["split"] == "train"]
test = pd.read_csv(os.path.join(ROOT, "data", "test", "test_sf.csv"))
HOSTEL = "mujhe kl mere roomate ne mara , mn eik girls hostel mn rehte hoon , mujhe bohat choot lage hai and us ne dhamki de hai k agar mnn n euska kaam na kiya tw wo mujhe phir mare gey , kl raat 8 15  pe ye sabh huwa"
def run(name, tr, norm):
    pp.ROMAN_URDU_MAP.clear(); pp.ROMAN_URDU_MAP.update(norm)
    m = fit("lr", params, tr, labels)
    S = m.scores(list(test.text)); cls = list(m.mlb.classes_)
    gold = [set(json.loads(s)) for s in test.sections]
    order = np.argsort(-S, 1)
    top1 = np.array([cls[o[0]] in g for o, g in zip(order, gold)])
    top3 = np.array([bool(set(cls[i] for i in o[:3]) & g) for o, g in zip(order, gold)])
    ru = (test.language == "roman_ur").values; real = (test.source == "real").values
    h = m.scores([HOSTEL])[0]; hs = [cls[i] for i in np.argsort(-h)[:3]]
    print(f"{name:34s} n={len(tr):4d} top1={top1.mean():.3f} top3={top3.mean():.3f} RU_top1={top1[ru].mean():.3f} "
          f"EN_top1={top1[~ru].mean():.3f} real_top1={top1[real].sum()}/{real.sum()} hostel_top3={hs}")
    return dict(config=name, n_train=len(tr), top1=round(top1.mean(),4), top3=round(top3.mean(),4),
                roman_ur_top1=round(top1[ru].mean(),4), en_top1=round(top1[~ru].mean(),4))
base = [r for r in train if not r["id"].startswith("chat_") and r["source"] != "sc_pk"]
chat = [r for r in train if r["id"].startswith("chat_")]; sc = [r for r in train if r["source"] == "sc_pk"]
out = [run("A baseline (original data)", base, OLD),
       run("B + chat-spelling normaliser", base, FULL),
       run("C + 224 Roman Urdu chat stories", base + chat, FULL),
       run("D + 142 Supreme Court PK facts", base + sc, FULL),
       run("E all (B+C+D)", base + chat + sc, FULL)]
pp.ROMAN_URDU_MAP.clear(); pp.ROMAN_URDU_MAP.update(FULL)
pd.DataFrame(out).to_csv(os.path.join(ROOT, "results", "round2_ablation.csv"), index=False)
