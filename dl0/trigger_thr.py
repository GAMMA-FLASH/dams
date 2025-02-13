import argparse
from packets.waveform import twos_comp_to_int, int_to_twos_comp
import sys

MAX_N_ADC = 16383

def parser():
    # Crea il parser
    parser = argparse.ArgumentParser(
        description="Script per lanciare un'operazione su HV o LV con una soglia di tensione."
    )
    
    # Aggiungi argomenti obbligatori
    parser.add_argument(
        "mode", 
        choices=["HV", "LV"], 
        help="Modalità di esecuzione: 'HV' per alta tensione o 'LV' per bassa tensione."
    )
    parser.add_argument(
        "volt_threshold", 
        type=float, 
        help="Soglia di tensione in volt. Deve essere un numero valido."
    )
    
    # Se non ci sono argomenti, mostra l'aiuto
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parsing degli argomenti
    args = parser.parse_args()

    # Operazioni basate sugli argomenti
    mode = args.mode
    if mode == 'HV':
        vpp = 40
    elif mode == 'LV':
        vpp = 2

    threshold = args.volt_threshold

    # Stampa i valori per verificare
    print(f"Modalità: {mode}, tensione pp {vpp}V")
    print(f"Soglia di tensione: {threshold}V")

    return vpp, threshold

    # Aggiungi qui la logica del tuo script
    # Esempio: funzione_di_analisi(mode, threshold)

if __name__ == "__main__":

    vpp, threshold_volt = parser()

    scale = vpp/MAX_N_ADC

    raw = int(threshold_volt/scale)

    c2 = int_to_twos_comp(raw, 14)

    print('Level %10.4f [V] = %d [-]' % (threshold_volt, c2))
