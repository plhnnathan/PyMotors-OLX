import requests
from unidecode import unidecode

class ConsultorFipe:
    def __init__(self):
        self.base_url = "https://parallelum.com.br/fipe/api/v1"
        self.headers = {"User-Agent": "PyMotors/3.0"}

    def obter_preco_medio(self, termo_busca: str, ano: int) -> tuple[float, str]:
        if not ano: 
            return 0.0, "Ano não informado."
        
        print(f"\n📊 FIPE: {termo_busca} ({ano})...")
        
        termos = termo_busca.split()
        if not termos: return 0.0, "Termo inválido."
        
        provavel_marca = unidecode(termos[0].lower())
        provavel_modelo = unidecode(" ".join(termos[1:]).lower()) if len(termos) > 1 else ""

        try:
            resp = requests.get(f"{self.base_url}/carros/marcas", headers=self.headers)
            marcas = resp.json()
            
            id_marca = None
            for m in marcas:
                if provavel_marca == unidecode(m['nome'].lower()):
                    id_marca = m['codigo']
                    break
            if not id_marca:
                for m in marcas:
                    if provavel_marca in unidecode(m['nome'].lower()):
                        id_marca = m['codigo']
                        break

            if not id_marca:
                return 0.0, f"Marca '{provavel_marca}' não encontrada."

            resp = requests.get(f"{self.base_url}/carros/marcas/{id_marca}/modelos", headers=self.headers)
            modelos = resp.json()['modelos']
            
            modelos_candidatos = []
            for mod in modelos:
                nome_mod = unidecode(mod['nome'].lower())
                if all(parte in nome_mod for parte in provavel_modelo.split()):
                    modelos_candidatos.append(mod)

            if not modelos_candidatos:
                return 0.0, f"Modelo '{provavel_modelo}' não existe."

            precos = []
            anos_encontrados = set()
            
            for mod in modelos_candidatos[:50]: 
                cod_modelo = mod['codigo']
                try:
                    resp = requests.get(f"{self.base_url}/carros/marcas/{id_marca}/modelos/{cod_modelo}/anos", headers=self.headers)
                    anos_disponiveis = resp.json()
                    
                    for a in anos_disponiveis:
                        txt_ano = a['nome'].split(" ")[0]
                        if txt_ano.isdigit():
                            anos_encontrados.add(txt_ano)

                    cod_ano = None
                    for a in anos_disponiveis:
                        if str(ano) in a['nome']:
                            cod_ano = a['codigo']
                            break
                    
                    if cod_ano:
                        resp_valor = requests.get(f"{self.base_url}/carros/marcas/{id_marca}/modelos/{cod_modelo}/anos/{cod_ano}", headers=self.headers)
                        dados = resp_valor.json()
                        valor = float(dados['Valor'].replace("R$", "").replace(".", "").replace(",", ".").strip())
                        precos.append(valor)
                except:
                    continue

            if precos:
                media = sum(precos) / len(precos)
                msg = f"Média de {len(precos)} versões."
                return media, msg
            else:
                lista_anos = sorted(list(anos_encontrados), reverse=True)[:5]
                dica = ", ".join(lista_anos)
                if dica:
                    return 0.0, f"Não existe em {ano}.\nTente: {dica}..."
                else:
                    return 0.0, f"Ano {ano} indisponível."

        except Exception:
            return 0.0, "Erro de conexão FIPE."