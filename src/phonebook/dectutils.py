import logging

logger = logging.getLogger("bornhack.%s" % __name__)


class DectUtils:
    """
    This class contains dect number <> letter related utilities
    """

    DECT_MATRIX = {
        "0": ["0"],
        "1": ["1"],
        "2": ["2", "A", "B", "C"],
        "3": ["3", "D", "E", "F"],
        "4": ["4", "G", "H", "I"],
        "5": ["5", "J", "K", "L"],
        "6": ["6", "M", "N", "O"],
        "7": ["7", "P", "Q", "R", "S"],
        "8": ["8", "T", "U", "V"],
        "9": ["9", "W", "X", "Y", "Z"],
    }

    def __init__(self):
        """
        Build a reverse lookup matrix based on self.DECT_MATRIX
        """
        self.REVERSE_DECT_MATRIX = {}
        for digit in self.DECT_MATRIX.keys():
            for letter in self.DECT_MATRIX[digit]:
                self.REVERSE_DECT_MATRIX[letter] = digit

    def get_dect_letter_combinations(self, numbers):
        """
        Generator to recursively get all combinations of letters for this number
        """
        # loop over the possible letters for the first digit
        for letter in self.DECT_MATRIX[numbers[0]]:
            # if we have more digits..
            if len(numbers) > 1:
                # call recursively with the remaining digits, and loop over the result
                for nextletter in self.get_dect_letter_combinations(numbers[1:]):
                    yield letter + nextletter
            else:
                # no more digits left, just yield the current letter
                yield letter

    def letters_to_number(self, letters):
        """
        Coverts "TYKL" to "8955"
        """
        result = ""
        for letter in letters:
            result += self.REVERSE_DECT_MATRIX[letter.upper()]
        return result

    def hex_ipui_ipei(self, ipui):
        if len(ipui) == 10:
            emc_hex = ipui[:5]
            psn_hex = ipui[-5:]
            emc = int(emc_hex, 16)
            psn = int(psn_hex, 16)
            return [emc, psn]
        else:
            return []

    def format_ipei(self, emc, psn):
        emc_s = str(emc).zfill(5)
        psn_s = str(psn).zfill(7)
        return f"{emc_s} {psn_s}"
