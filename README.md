# Kitchen CAD - Mittatarkka keittiösuunnittelu

Ilmainen, avoimen lähdekoodin keittiösuunnittelujärjestelmä Windowsille.

## Teknologia
- **CAD**: FreeCAD (Python API)
- **API**: FastAPI
- **Formaatti**: DXF (mittatarkka 2D)

## Asennus

1. Asenna FreeCAD: https://www.freecad.org/downloads.php 
2. Asenna Python-riippuvuudet:
   ```bash
   pip install fastapi uvicorn ezdxf
python cad/generate_kitchen.py
uvicorn api.main:app --reload
kitchen-cad/
  api/         # FastAPI-palvelin
  cad/         # FreeCAD Python-skriptit
  rules/       # Keittiösäännöt ja validointi
  catalog/     # Moduulit ja laitteet JSONina
  out/         # Generoidut DXF-tiedostot (gitignore)
