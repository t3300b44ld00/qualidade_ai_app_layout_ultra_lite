import statistics

class AnomalyDetector:
    """
    Detector robusto leve, sem dependências. Usa mediana e desvio absoluto mediano (MAD).
    """
    def __init__(self, db):
        self.db = db
        self.medians = None
        self.mads = None
        self.fields = ["status_bin", "obs_len", "item_len"]

    def _features(self, r: dict) -> list[float]:
        status_bin = 1.0 if str(r.get("status","")).lower().startswith("aprov") else 0.0
        obs_len = float(len(r.get("observacoes") or ""))
        item_len = float(len(r.get("item") or ""))
        return [status_bin, obs_len, item_len]

    def fit(self) -> int:
        rows = self.db.search_inspecoes("")
        if not rows:
            raise RuntimeError("Sem dados para treinar.")
        feats = [self._features(r) for r in rows]
        cols = list(zip(*feats))
        self.medians = [statistics.median(c) for c in cols]
        # MAD aproximado
        self.mads = []
        for j, c in enumerate(cols):
            med = self.medians[j]
            mad = statistics.median([abs(x - med) for x in c]) or 1.0
            self.mads.append(mad)
        return len(rows)

    def is_anomaly(self, registro: dict, thresh: float = 3.5) -> bool:
        if self.medians is None or self.mads is None:
            raise RuntimeError("Treine o modelo primeiro.")
        x = self._features(registro)
        robust_z = [abs((x[i] - self.medians[i]) / self.mads[i]) for i in range(len(x))]
        return max(robust_z) > thresh
