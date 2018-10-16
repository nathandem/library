def strip_nonascii(string):
    """
    Sanitize the given unicode string by removing all special
    Western characters from it. Not extensive.
    """
    special_chars = 'àáâãäåçèéêëìíîïñòóôõöøšùúûüýÿÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØŠÙÚÛÜÝŸ'
    converted_chars = 'aaaaaaceeeeiiiinoooooosuuuuyyAAAAAACEEEEIIIINOOOOOOSUUUUYY'

    complex_conversion_table = {'æ': 'ae', 'œ': 'oe', 'Æ': 'AE', 'Œ': 'OE'}

    return ''.join(
        complex_conversion_table[c] if c in complex_conversion_table
        else converted_chars[special_chars.find(c)] if c in special_chars
        else c
        for c in string
    )
