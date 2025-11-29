import json
import csv
from pathlib import Path
from docx import Document
from openai import OpenAI
from config import NVIDIA_API_SC

class SmetaParser:
    """Библиотека для парсинга DOCX смет в JSON с MCC кодами"""
    
    def __init__(self, api_key=None, mcc_csv_path="examples/mcc_codes.csv"):
        self.api_key = api_key or NVIDIA_API_SC
        self.mcc_csv_path = mcc_csv_path
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )
        
        self.mcc_codes = self._load_mcc_codes()
    
    def _load_mcc_codes(self):
        """Загружает MCC коды из CSV"""
        mcc_data = []
        try:
            with open(self.mcc_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mcc_data.append(f"{row['MCC']}: {row['Название']} - {row['Описание']}")
        except FileNotFoundError:
            print(f"Внимание: файл {self.mcc_csv_path} не найден")
        return mcc_data
    
    def _read_docx(self, file_path):
        """Читает DOCX файл"""
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    def _create_prompt(self, smeta_text):
        """Создает промпт для нейросети"""
        mcc_list = "\n".join(self.mcc_codes)
        
        return f"""Преобразуй смету в JSON. Для каждой категории юрлиц подбери ВСЕ релевантные MCC коды.

СМЕТА:
{smeta_text}

MCC КОДЫ:
{mcc_list}

СТРУКТУРА allowed_categories:
- Для legal_entities: [{{"category": "название", "mcc_codes": ["код1", "код2"]}}]
- Для individuals: ["строка1", "строка2"]

ПОДБОР MCC:
- Научное/медицинское оборудование → 5047, 5094, 5122
- Компьютеры → 5732, 5734, 5045
- Химические реагенты → 5169, 5085, 5984
- Лабораторные услуги → 8071, 8099
- Расходные материалы → 5111, 5198, 5199
- Тестирование → 8734

JSON:
{{
  "grant_metadata": {{
    "name": "название",
    "total_budget": число,
    "currency": "RUB",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "duration_months": число,
    "payment_system": "Мир"
  }},
  "stages": [
    {{
      "stage_id": число,
      "stage_name": "название",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "duration_months": число,
      "stage_budget": число,
      "status": "planned",
      "spending_rules": [
        {{
          "rule_id": "id",
          "rule_type": "individuals" или "legal_entities",
          "rule_name": "название",
          "limit": число,
          "allowed_categories": [...],
          "transactions": []
        }}
      ]
    }}
  ],
  "summary": {{
    "total_spent": 0,
    "total_remaining": бюджет,
    "spending_by_type": {{"individuals": 0, "legal_entities": 0}},
    "spending_by_stage": {{}},
    "last_updated": "2025-11-28T20:11:00Z"
  }}
}}

Верни ТОЛЬКО JSON."""
    
    def _extract_json(self, text):
        """Извлекает JSON из ответа"""
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except:
                return None
        return None
    
    def parse(self, docx_path, verbose=True):
        """
        Парсит DOCX смету в JSON
        
        Args:
            docx_path (str): путь к DOCX файлу
            verbose (bool): выводить ли прогресс
        
        Returns:
            dict: JSON структура сметы или None при ошибке
        """
        if verbose:
            print(f"Читаю {docx_path}...")
        
        smeta_text = self._read_docx(docx_path)
        
        if verbose:
            print(f"Прочитано {len(smeta_text)} символов")
            print("Генерация JSON...")
        
        prompt = self._create_prompt(smeta_text)
        
        completion = self.client.chat.completions.create(
            model="deepseek-ai/deepseek-v3.1-terminus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.15,
            top_p=0.7,
            max_tokens=10000,
            stream=True
        )
        
        response = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                if verbose:
                    print(".", end="", flush=True)
        
        if verbose:
            print("\nГотово")
        
        result = self._extract_json(response)
        
        if not result and verbose:
            print("Ошибка парсинга JSON")
            with open("debug_response.txt", "w", encoding="utf-8") as f:
                f.write(response)
        
        return result


# Простая функция для быстрого использования
def parse_smeta(docx_path, output_json_path=None, verbose=True):
    """
    Быстрый парсинг сметы
    
    Args:
        docx_path (str): путь к DOCX файлу
        output_json_path (str): куда сохранить JSON (опционально)
        verbose (bool): выводить прогресс
    
    Returns:
        dict: JSON структура сметы
    """
    parser = SmetaParser()
    result = parser.parse(docx_path, verbose=verbose)
    
    if result and output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"JSON сохранен в {output_json_path}")
    
    return result
