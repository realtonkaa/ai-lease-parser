# AI Lease Parser

A Python tool that extracts structured data from residential lease PDFs using OCR and AI. Point it at a lease document and get back a clean spreadsheet with rent amounts, dates, tenant names, and more.

---

## Why I Built This

Landlords and property managers waste hours manually typing lease data into spreadsheets. When you manage dozens of properties, re-keying tenant names, rent amounts, start dates, and deposit figures from PDFs is tedious and error-prone.

I built this tool to automate that workflow. Drop in a lease PDF, get back a structured CSV or Excel file with every key field extracted and validated. No more copying numbers by hand.

---

## Features

- Extracts 13 structured fields from residential lease agreements
- Works on digital PDFs (pdfplumber) and scanned documents (OCR via pytesseract)
- Regex extraction works without any API key or internet connection
- Optional OpenAI LLM mode for higher accuracy on unusual formats
- Batch processing: feed a folder of leases, get one output file
- Validation: catches bad dates, impossible rent amounts, missing required fields
- Exports to CSV or Excel (.xlsx)
- Streamlit web UI with drag-and-drop upload and inline field editing

### Extracted Fields

| Field | Type | Required |
|---|---|---|
| tenant_name | string | yes |
| landlord_name | string | yes |
| property_address | string | yes |
| monthly_rent | float | yes |
| security_deposit | float | yes |
| lease_start_date | date | yes |
| lease_end_date | date | yes |
| late_fee_amount | float | no |
| late_fee_grace_period | int | no |
| pet_policy | string | no |
| utilities_included | list | no |
| parking | string | no |
| renewal_terms | string | no |

---

## Installation

```bash
git clone https://github.com/realtonkaa/ai-lease-parser.git
cd ai-lease-parser
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

For OCR support on scanned PDFs, also install Tesseract:
- Ubuntu: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: Download the installer from https://github.com/UB-Mannheim/tesseract/wiki

---

## Usage

### CLI

Process a single lease:
```bash
python -m src.cli lease.pdf --output results.csv
```

Process a folder of leases:
```bash
python -m src.cli leases_folder/ --output all_leases.xlsx
```

Use LLM extraction (requires `OPENAI_API_KEY`):
```bash
export OPENAI_API_KEY=sk-...
python -m src.cli leases_folder/ --output results.xlsx --use-llm
```

### Web UI

```bash
streamlit run app/app.py
```

Then open http://localhost:8501 in your browser. Drag and drop lease PDFs, review extracted fields, edit any corrections, and download as CSV or Excel.

---

## How It Works

1. **PDF reading** — pdfplumber extracts text layer from digital PDFs. If the text is sparse (scanned document), pytesseract OCR reads the page images instead.

2. **Regex extraction** — A set of patterns tuned for common lease language pulls out fields like rent amounts, dates, and names from the raw text. This works offline with no API calls.

3. **LLM extraction (optional)** — When `--use-llm` is passed and `OPENAI_API_KEY` is set, the text is sent to OpenAI GPT-4o-mini with a structured prompt. The LLM result is merged with the regex result, preferring whichever has higher confidence.

4. **Validation** — Extracted values are checked: dates must be parseable and end > start, rent must be between $100 and $50,000/month, deposit should not exceed 3x rent, required fields must be present.

5. **Export** — Results are written to CSV or Excel with one row per lease.

---

## Example Output

```
source_file,tenant_name,landlord_name,property_address,monthly_rent,security_deposit,...
sample_lease_1.txt,Maria Garcia,Robert J. Henderson,"742 Evergreen Terrace, Apt 3B, Springfield, IL 62704",1450.0,2900.0,...
sample_lease_2.txt,James T. Wilson and Sarah K. Wilson,Greenfield Property Management LLC,"1500 Oak Boulevard, Unit 7, Austin, TX 78701",2100.0,2100.0,...
```

---

## Limitations

- Regex extraction works best on standard lease formats. Highly unusual layouts may miss fields.
- OCR quality depends on the scan resolution of the source document.
- Date parsing covers common English formats. Non-English leases are not supported.
- LLM extraction requires an OpenAI API key and incurs API costs (~$0.01 per lease with gpt-4o-mini).
- The tool extracts data as-is; it does not interpret legal language or give legal advice.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Built With Claude

I used [Claude](https://claude.ai) (Anthropic's AI assistant) as a development partner on this project. Claude helped me with:

- Designing the field extraction architecture and deciding which lease fields matter most
- Writing regex patterns that handle the dozen different ways landlords format leases
- Building validation logic for dates, rent ranges, and deposit ratios
- Structuring the test suite across 5 modules

The project concept came from watching a property manager spend hours retyping lease data into spreadsheets. I designed the tool, chose the OCR + regex + LLM hybrid approach, and made all architecture decisions. Claude helped me implement faster and catch edge cases I would have missed.

---

## License

MIT License. See LICENSE for details.
