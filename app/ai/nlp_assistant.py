import re

class QnAAssistant:
    def __init__(self, db):
        self.db = db

    def _tok(self, s: str) -> set[str]:
        return set(re.findall(r"[a-zA-ZÀ-ÿ0-9]+", s.lower()))

    def answer(self, q: str) -> str:
        qtok = self._tok(q)
        rows = self.db.search_inspecoes("")
        if not rows:
            return "Cadastre algumas inspeções para começar."
        scored = []
        for r in rows:
            text = " ".join([
                str(r.get("item", "")),
                str(r.get("responsavel", "")),
                str(r.get("status", "")),
                str(r.get("observacoes", "")),
            ])
            score = len(qtok.intersection(self._tok(text)))
            scored.append((score, r))
        scored.sort(reverse=True, key=lambda x: x[0])
        top = [r for s, r in scored[:5] if s > 0]
        if not top:
            return "Sem correspondências diretas. Tente incluir item, responsável ou status."
        lines = [
            f"{r['id']}. {r['item']} por {r['responsavel']}. Status {r['status']}. Obs {r.get('observacoes','')}"
            for r in top
        ]
        return "Resultados:\n" + "\n".join(lines)
