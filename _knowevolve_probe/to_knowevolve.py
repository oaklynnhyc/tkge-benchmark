#!/usr/bin/env python3
"""my data -> Know-Evolve 輸入格式（feasibility probe，獨立於主管線）。

Know-Evolve（rstriv/Know-Evolve）dataset.cpp::LoadEvents 讀法：
    fs >> subject >> rel >> object >> t ; 然後 LoadFeat: n_feat, [feat_id feat_val]*n_feat
所以每筆 = `subject  rel  object  t  n_feat`（本資料無特徵→n_feat=0）。
- id 皆 0-indexed 整數；subject/object 共用同一 entity 空間；assert id<num_entities/num_rels。
- 檔案需「依 t 由小到大排序」（模型靠事件順序建 prev_event 鏈）。
- meta(stat.txt) = `num_entities  num_rels  0`。
- 原 repo 腳本只用 train/test（無 valid）→ 這裡把 valid 併入 train。

輸出：_knowevolve_probe/data_ready/<ds>/{train.txt,test.txt,stat.txt} + map_meta.json
"""
import csv, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]   # tkge-benchmark/
SRC = ROOT / "data_source"
OUT = pathlib.Path(__file__).resolve().parent / "data_ready"

def rows(ds, split):
    out = []
    with open(SRC / ds / f"{split}.tsv") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            s, rel, o = r["subject"].strip(), r["relation"].strip(), r["object"].strip()
            if ds == "finreflect":
                t = int(r["year"].strip())
            else:
                tcol = "date" if "date" in r else "datetime"
                t = int(r["time_step"].strip()) if "time_step" in r else None
                if t is None:  # 後備：用日期序數
                    t = r[tcol].strip()
            if s and o and rel and s != o:        # 去自迴圈（論文：無 self-loop）
                out.append((s, rel, o, t))
    return out

def convert(ds):
    tr = rows(ds, "train") + rows(ds, "valid")    # KE 無 valid → 併入 train
    te = rows(ds, "test")
    allr = tr + te
    # 時間正規化成 0 起算整數
    tmin = min(int(x[3]) for x in allr)
    def ti(x): return int(x[3]) - tmin
    # 共用 entity map（subject ∪ object，跨所有 split）
    ents = sorted({x[0] for x in allr} | {x[2] for x in allr})
    rels = sorted({x[1] for x in allr})
    eid = {e: i for i, e in enumerate(ents)}
    rid = {r: i for i, r in enumerate(rels)}
    dst = OUT / ds; dst.mkdir(parents=True, exist_ok=True)
    def write(name, data):
        data = sorted(data, key=lambda x: ti(x))   # 依時間排序（KE 必須）
        with open(dst / name, "w") as f:
            for s, r, o, _ in data:
                f.write(f"{eid[s]}\t{rid[r]}\t{eid[o]}\t{ti((s,r,o,_))}\t0\n")
    write("train.txt", tr); write("test.txt", te)
    with open(dst / "stat.txt", "w") as f:
        f.write(f"{len(ents)}\t{len(rels)}\t0\n")
    meta = {"dataset": ds, "num_entities": len(ents), "num_relations": len(rels),
            "time_min": tmin, "time_max": max(int(x[3]) for x in allr),
            "n_time_steps": len({ti(x) for x in allr}),
            "train": len(tr), "test": len(te), "note": "valid 併入 train；無 self-loop；t 已 0 起算整數"}
    json.dump(meta, open(dst / "map_meta.json", "w"), ensure_ascii=False, indent=2)
    print(ds, meta)

if __name__ == "__main__":
    for ds in (sys.argv[1:] or ["finreflect", "icews18", "gdelt"]):
        convert(ds)
