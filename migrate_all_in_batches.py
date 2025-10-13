#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecuta migración completa en lotes de 500 propiedades
"""
import sys
import subprocess
import time

def main():
    total_props = 2498
    batch_size = 500
    offset = 0

    print("="*80)
    print(f"MIGRACIÓN COMPLETA EN LOTES DE {batch_size}")
    print(f"Total propiedades: {total_props}")
    print("="*80)

    # Archivar primero (solo una vez)
    print("\n🗂️  Paso 1: ARCHIVANDO propiedades existentes...")
    result = subprocess.run(
        [sys.executable, "migrate_archive_and_create.py", "0"],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"⚠️  Error archivando: {result.stderr}")

    # Crear en lotes
    batch_num = 1
    while offset < total_props:
        current_batch = min(batch_size, total_props - offset)

        print("\n" + "="*80)
        print(f"LOTE {batch_num}: Propiedades {offset+1} a {offset+current_batch}")
        print("="*80)

        # Modificar script temporalmente para usar offset
        import json
        batch_script = f"""
import sys
sys.path.insert(0, '.')
from migrate_archive_and_create import ArchiveAndCreateMigrator

migrator = ArchiveAndCreateMigrator()
migrator.migrate(limit={current_batch}, offset={offset}, archive_first=False)
"""

        with open('temp_batch.py', 'w', encoding='utf-8') as f:
            f.write(batch_script)

        start_time = time.time()
        result = subprocess.run(
            [sys.executable, "temp_batch.py"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600  # 10 minutos por lote
        )
        elapsed = time.time() - start_time

        print(result.stdout)
        if result.returncode != 0:
            print(f"⚠️  Error en lote {batch_num}: {result.stderr}")

        print(f"\n⏱️  Tiempo lote {batch_num}: {elapsed:.1f}s")

        offset += batch_size
        batch_num += 1
        time.sleep(2)  # Pausa entre lotes

    print("\n" + "="*80)
    print("✅ MIGRACIÓN COMPLETA FINALIZADA")
    print("="*80)

if __name__ == "__main__":
    main()
