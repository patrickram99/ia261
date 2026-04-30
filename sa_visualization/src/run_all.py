"""
Script maestro: ejecuta todo y genera todos los outputs.
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script):
    print(f"\n{'='*60}\n>>> {script}\n{'='*60}")
    r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                       capture_output=False)
    if r.returncode != 0:
        print(f"!!! Error en {script}")
        sys.exit(r.returncode)


if __name__ == "__main__":
    run("viz_funcion.py")
    run("viz_tsp.py")
    run("comparativa.py")
    run("analisis_hiperparametros.py")
    print("\nTodos los outputs generados en sa_visualization/outputs/")
