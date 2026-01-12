# PyMotors - AI Auto Scout 🚗

This project is a Python-based **Data Mining & Analysis** tool designed to scout vehicle listings from public marketplaces (OLX). It acts as an intelligent consultant, extracting raw data, enriching it with official market values (FIPE), and detecting opportunities or risks for the user.

## ⚙️ Key Features
* **Extraction (Scraping):**
    * Real-time extraction of vehicle listings using `curl_cffi` to handle TLS fingerprints and avoid anti-bot blocks.
    * Dynamic filtering by State (UF), City, Engine type, and Year range.
* **Transformation (Analysis):**
    * **FIPE Integration:** Automatically identifies the vehicle version and fetches the official market price via API.
    * **Smart Scoring:** Classifies deals as "Excellent" (Green), "Fair", or "Expensive" based on FIPE comparison.
    * **Risk Detection:** Scans descriptions for keywords like "Leilão" (Auction), "Sinistro" (Accident), or "RS".
    * **Usage Metrics:** Calculates average KM/Year to identify high-usage vehicles (e.g., ex-taxis).
* **Loading (Visualization):**
    * **Modern GUI:** A clean, responsive desktop interface built with `CustomTkinter` (Light/Dark mode).
    * **Excel Reports:** Generates professional `.xlsx` files with conditional formatting and active hyperlinks.

## 🛠️ Technologies & Skills
* **Language:** Python 3.10+
* **Libraries:** CustomTkinter (GUI), Pandas & XlsxWriter (Data), Curl_cffi & BeautifulSoup4 (Scraping).
* **Concepts:** Object-Oriented Programming (OOP), Multi-threading, API Integration, ETL Pipelines.

## 📁 Project Structure
* `src/`: Contains the core modules:
    * `scraper.py`: Logic for extracting data from the web.
    * `analyser.py`: Intelligence layer (FIPE comparison & tagging).
    * `fipe.py`: API client for official car pricing.
    * `models.py`: Data validation using Pydantic.
* `data/`: Directory where the Excel reports are saved.
* `main_app.py`: Application entry point (GUI).

## 📧 Contact
Nathan Chaia | [LinkedIn](https://www.linkedin.com/in/nathan-chaia-ba57773a2)