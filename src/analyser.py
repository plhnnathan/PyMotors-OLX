from datetime import datetime
from src.models import Anuncio

class AnalisadorVeiculo:
    def __init__(self, fipe_referencia: float = 0):
        self.fipe = fipe_referencia
        self.ano_atual = datetime.now().year
        self.red_flags = ["leilao", "leilão", "sinistro", "batido", "consta", "recuperado", "csv", "remarcado", "chassi"]

    def analisar(self, anuncio: Anuncio) -> Anuncio:
        tags = []
        texto_completo = f"{anuncio.titulo}".lower()

        for flag in self.red_flags:
            if flag in texto_completo:
                tags.append(f"⚠️ ALERTA: {flag.upper()}")
                anuncio.score_preco = "Cuidado"

        if self.fipe > 0 and anuncio.preco > 0:
            diferenca = anuncio.preco - self.fipe
            porcentagem = (diferenca / self.fipe) * 100
            
            if porcentagem < -15:
                tags.append(f"💰 {abs(int(porcentagem))}% Abaixo da Fipe")
                if "⚠️" not in str(tags): 
                    anuncio.score_preco = "Excelente"
                else:
                    tags.append("❓ Preço suspeito")
            elif porcentagem < 0:
                tags.append("✅ Abaixo da Fipe")
                anuncio.score_preco = "Bom"
            elif porcentagem > 15:
                tags.append("📈 Acima da Fipe")
                anuncio.score_preco = "Caro"

        if anuncio.ano and anuncio.km:
            idade = self.ano_atual - anuncio.ano
            idade = 1 if idade == 0 else idade
            
            km_por_ano = anuncio.km / idade
            anuncio.km_anual = int(km_por_ano)
            
            if km_por_ano > 25000:
                tags.append("🚕 Alta Rodagem (+25k/ano)")
            elif km_por_ano < 5000 and idade > 2:
                tags.append("💎 Baixa Rodagem")

        anuncio.tags = tags
        return anuncio