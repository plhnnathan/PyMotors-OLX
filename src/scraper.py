import json
from typing import List, Optional
from curl_cffi import requests
from bs4 import BeautifulSoup
from src.models import Anuncio

class OLXScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.olx.com.br/"
        }

    def buscar(self, termo: str, paginas: int = 1, 
               min_price: Optional[int] = None, max_price: Optional[int] = None,
               min_year: Optional[int] = None, max_year: Optional[int] = None,
               estado: Optional[str] = None) -> List[Anuncio]:
        
        todos_anuncios = []
        base_url = "https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios"
        
        if estado and len(estado) == 2 and estado.upper() != "BR":
            base_url = f"{base_url}/estado-{estado.lower()}"

        print(f"🌍 Região da busca: {estado if estado else 'Brasil'}")

        for page in range(1, paginas + 1):
            print(f"🔎 Buscando '{termo}' (Página {page})...")
            
            params = {"q": termo, "o": page}
            if min_price: params["ps"] = min_price
            if max_price: params["pe"] = max_price
            if min_year:  params["rs"] = min_year
            if max_year:  params["re"] = max_year

            try:
                response = requests.get(
                    base_url, params=params, headers=self.headers, 
                    impersonate="chrome120", timeout=15
                )

                if response.status_code == 200:
                    novos = self._parse_html(response.text)
                    todos_anuncios.extend(novos)
                    if not novos:
                        break
                else:
                    print(f"❌ Erro HTTP {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Erro de Conexão: {e}")

        return todos_anuncios

    def _parse_html(self, html: str) -> List[Anuncio]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            script = soup.find("script", {"id": "__NEXT_DATA__"})
            if not script: return []

            data = json.loads(script.string)
            try:
                ads_list = data["props"]["pageProps"]["ads"]
            except KeyError:
                return []

            resultados = []
            for item in ads_list:
                if not isinstance(item, dict) or "subject" not in item:
                    continue

                try:
                    props_raw = item.get("properties") or []
                    mapa_props = {p.get("name"): p.get("value") for p in props_raw if isinstance(p, dict)}

                    imgs = item.get("images")
                    img_url = imgs[0].get("url") if (isinstance(imgs, list) and len(imgs) > 0) else None

                    loc = item.get("location", {})
                    cidade = loc.get("municipality", "")
                    estado = loc.get("uf", "")
                    
                    if not cidade:
                        loc_det = item.get("locationDetails", {})
                        cidade = loc_det.get("municipality", "")
                        estado = loc_det.get("uf", "")

                    anuncio = Anuncio(
                        id=str(item.get("listId", "")),
                        titulo=item.get("subject", ""),
                        preco=item.get("price", "0"),
                        ano=int(mapa_props.get("regdate", 0)), 
                        km=int(mapa_props.get("mileage", 0)),
                        cambio=mapa_props.get("gearbox", "N/A"),
                        combustivel=mapa_props.get("fuel", "N/A"),
                        cidade=cidade,
                        estado=estado,
                        link=item.get("url", ""),
                        imagem=img_url,
                        data_publicacao=item.get("listTime", "")
                    )
                    resultados.append(anuncio)
                except Exception:
                    continue
            return resultados
        except Exception:
            return []