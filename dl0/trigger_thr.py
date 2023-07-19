from waveform import twos_comp_to_int, int_to_twos_comp
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Indicare il valore in volt come argomento.")
        sys.exit(1)

    volt = float(sys.argv[1])

    scale = 2/16383

    raw = int(volt/scale)

    c2 = int_to_twos_comp(raw, 14)

    print('Level %10.4f [V] = %d [-]' % (volt, c2))
