from PIL import Image
import sys
import random as rd
import string


def text_to_bits(text, encoding='utf-8', errors='surrogatepass'):
    bits = bin(int.from_bytes(text.encode(encoding, errors), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))


def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode(encoding, errors) or '\0'


def hidemsg(msg, image, name):
    bits = list(map(int, list(text_to_bits(msg))))  # message converted to bits
    size = list(map(int, list(bin(len(bits))[2:])))  # size of the message converted to bits, represented on 8 bits
    toadd = MAX_INDEX_SIZE * 4 - len(size)
    for i in range(toadd):
        size.insert(0, 0)

    if usekey2:
        key2 = generateprintablekey(len(msg))
        bits = xor(bits, printablekeytoxor(key2))
    elif usekey1:
        key1 = generatexorkey(len(bits))
        bits = xor(bits, key1)

    data = list(image.getdata())
    bitslen = len(bits)
    broken = False
    for index, pixel in enumerate(data):
        pixel = list(pixel)
        if index < MAX_INDEX_SIZE:
            for i in range(4):
                if pixel[i] % 2 != size[i + 4 * index]:
                    if size[i + 4 * index] == 0:
                        pixel[i] -= 1
                    else:
                        pixel[i] += 1
            data[index] = tuple(pixel)
        else:
            for i in range(4):
                if bitslen < i + 4 * (index - MAX_INDEX_SIZE) + 1:  # we are done hiding the message
                    broken = True
                    break
                if pixel[i] % 2 != bits[i + 4 * (index - MAX_INDEX_SIZE)]:
                    if bits[i + 4 * (index - MAX_INDEX_SIZE)] == 0:
                        pixel[i] -= 1
                    else:
                        pixel[i] += 1
            data[index] = tuple(pixel)
            if broken:
                break
    newimage = Image.new(image.mode, image.size)
    newimage.putdata(data)
    newimage.save(name + ".PNG", image.format)
    print("Message hidden. output : " + name + ".PNG")
    if usekey1:
        print("Encrypted with secret key : " + intarraytostr(key1))
    elif usekey2:
        print("Encrypted with secret key : " + key2)


def intarraytostr(array):
    res = ""
    for val in array:
        res += str(val)
    return res


def xor(in1, in2):
    res = ""
    for index, val in enumerate(in1):
        bool = (val and not in2[index]) or (in2[index] and not val)
        if bool:
            res += "1"
            continue
        res += "0"
    return list(map(int, res))


def getmsg(image, secretkey):
    if secretkey:
        secretkey = list(map(int, secretkey))
    msg = ""
    size = ""
    data = list(image.getdata())
    count = 0
    broken2 = False
    for index, pixel in enumerate(data):
        if index < MAX_INDEX_SIZE:
            for i in range(4):
                size += str(pixel[i] % 2)

        else:
            if index == MAX_INDEX_SIZE:
                size = int(size, 2)
            for i in range(4):
                msg += str(pixel[i] % 2)
                count += 1
                if count == size:
                    broken2 = True
                    break
            if broken2:
                break
    if secretkey:
        msg = list(map(int, list(msg)))
        xorres = xor(msg, secretkey)
        msg = intarraytostr(xorres)
    return text_from_bits(msg)


def encrypt(messg, filename, outp):
    try:
        hidemsg(messg, Image.open(filename), outp.split(".")[0])
    except:
        print("Error occured:")
        raise


def decrypt(inputfile, secretkey):
    try:
        msg = getmsg(Image.open(inputfile), list(secretkey))
        print("Found message: ")
        print(msg)
    except:
        print("Error occured:")
        raise


def generatexorkey(size):
    key = ""
    for i in range(size):
        key += str(rd.randint(0, 1))
    return list(map(int, list(key)))


def generateprintablekey(size):
    res = ""
    printables = string.printable.replace(" \t\n\r\x0b\x0c", "").replace("`", "").replace("^", "").replace("\"", "")
    for i in range(size):
        res += rd.choice(printables)
    return res


def printablekeytoxor(keystr):
    bits = text_to_bits(keystr)
    return list(map(int, list(bits)))


def recallusage(f):
    if f == "hide":
        print("Usage :\nsteg -hide -m msg -i image [-o outputfile] [-kb] [-ka] #hide msg in image. Use -ka or -kb to "
              "encrypt the message with a random key. ka yields an ascii printable key, easy to store but less "
              "secure. kb yields a bit sequence key : harder to store but more secure.")
    if f == "get":
        print("Usage : \nsteg -get -i image [-ka \"key\"] [-kb \"key\"] #get message from image. Use -ka or -kb to "
              "specify the key used during encryption. ka for an ascii key and kb for a bit sequence key. Quotes "
              "around the key are important.")
    if f == "all":
        print("Usage :\nsteg -hide -m msg -i image [-o outputfile] [-kb] [-ka] #hide msg in image. Use -ka or -kb to "
              "encrypt the message with a random key. ka yields an ascii printable key, easy to store but less "
              "secure. kb yields a bit sequence key : harder to store but more secure.")
        print("Usage : \nsteg -get -i image [-ka \"key\"] [-kb \"key\"] #get message from image. Use -ka or -kb to "
              "specify the key used during encryption. ka for an ascii key and kb for a bit sequence key. Quotes "
              "around the key are important.")


# ========================
# ========= MAIN =========
# ========================
MAX_INDEX_SIZE = 8
usekey1 = False
usekey2 = False

if len(sys.argv) < 2 or (sys.argv[1] != "-hide" and sys.argv[1] != "-get"):
    recallusage("all")
    sys.exit(-1)
else:
    # === HIDE THE MESSAGE ===
    if sys.argv[1] == "-hide":
        message = "hello"
        inputname = ""
        outputname = "output"
        if "-kb" in sys.argv:  # USE ENCRYPTION KEY AS BITS ?
            usekey1 = True
            usekey2 = False
        if "-ka" in sys.argv:  # USE ENCRYPTION KEY AS BITS ?
            usekey1 = False
            usekey2 = True
        if "-o" in sys.argv:  # OUTPUT NAME
            position = sys.argv.index("-o") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Output file name is missing.")
                recallusage("hide")
                sys.exit(-1)
            outputname = sys.argv[position]
        if "-m" in sys.argv:  # MESSAGE TO HIDE
            position = sys.argv.index("-m") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Message is missing.")
                recallusage("hide")
                sys.exit(-1)
            message = sys.argv[position]
        else:
            print("No message specified. Hiding 'hello'.")
        if "-i" not in sys.argv:  # INPUT COVER IMAGE
            print("Input file argument is missing.")
            recallusage("hide")
            sys.exit(-1)
        else:
            position = sys.argv.index("-i") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Input file name is missing.")
                recallusage("hide")
                sys.exit(-1)
            inputname = sys.argv[position]
        encrypt(message, inputname, outputname)
    # === RETRIEVE THE MESSAGE ===
    elif sys.argv[1] == "-get":
        inputname = ""
        key = ""
        if "-kb" in sys.argv:  # SECRET KEY
            position = sys.argv.index("-kb") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Key not specified.")
                recallusage("get")
                sys.exit(-1)
            key = sys.argv[position]
        if "-ka" in sys.argv:  # SECRET KEY
            position = sys.argv.index("-ka") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Key not specified.")
                recallusage("get")
                sys.exit(-1)
            key = text_to_bits(sys.argv[position])
        if "-i" not in sys.argv:  # INPUT IMAGE CONTAINING MESSAGE
            print("Input file argument is missing.")
            recallusage("get")
            sys.exit(-1)
        else:
            position = sys.argv.index("-i") + 1
            if position == len(sys.argv):  # last parameter is -o : missing the file name
                print("Input file name is missing.")
                recallusage("get")
                sys.exit(-1)
            inputname = sys.argv[position]
        decrypt(inputname, key)

sys.exit(0)
