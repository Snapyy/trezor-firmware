import utime

if False:
    from typing import Tuple


def format_amount(amount: int, decimals: int) -> str:
    if amount < 0:
        amount = -amount
        sign = "-"
    else:
        sign = ""
    d = pow(10, decimals)
    s = (
        ("%s%d.%0*d" % (sign, amount // d, decimals, amount % d))
        .rstrip("0")
        .rstrip(".")
    )
    return s


def format_ordinal(number: int) -> str:
    return str(number) + {1: "st", 2: "nd", 3: "rd"}.get(
        4 if 10 <= number % 100 < 20 else number % 10, "th"
    )


def format_plural(string: str, count: int, plural: str) -> str:
    """
    Adds plural form to a string based on `count`.
    !! Does not work with irregular words !!

    Example:
    >>> format_plural("We need {count} more {plural}", 3, "share")
    'We need 3 more shares'
    >>> format_plural("We need {count} more {plural}", 1, "share")
    'We need 1 more share'
    >>> format_plural("{count} {plural}", 4, "candy")
    '4 candies'
    """
    if not all(s in string for s in ("{count}", "{plural}")):
        # string needs to have {count} and {plural} inside
        raise ValueError

    if count == 0 or count > 1:
        if plural[-1] == "y":
            plural = plural[:-1] + "ies"
        elif plural[-1] in "hsxz":
            plural = plural + "es"
        else:
            plural = plural + "s"

    return string.format(count=count, plural=plural)


def format_duration_ms(milliseconds: int) -> str:
    """
    Returns human-friendly representation of a duration. Truncates all decimals.
    """
    units = (
        ("hour", 60 * 60 * 1000),
        ("minute", 60 * 1000),
        ("second", 1000),
    )
    for unit, divisor in units:
        if milliseconds >= divisor:
            break
    else:
        unit = "millisecond"
        divisor = 1

    return format_plural("{count} {plural}", milliseconds // divisor, unit)


def _calculate_timestamp_correction(timestamp: int) -> (Tuple[tuple, int]):
    """
    utime module can't convert timestamp to datetime with seconds precision.
    returns date in tuple format and correction in seconds
    from the utime-calculated date's midnight
    to the correct datetime
    Example:
        timestamp                   1616057224
        correct datetime            "2021-03-18 08:47:04"
        utime-calculated datetime   "2021-03-18 08:46:56"
        midnight datetime           "2021-03-18 00:00:00"
        returned date               (2021, 3, 18, 0, 0, 0, 3, 77, 0)
        correction                  31624 (~ 8:47:04)
    """
    approx_datetime = utime.localtime(timestamp)
    # filter date only, erase time
    date = approx_datetime[:3] + (0, 0, 0) + approx_datetime[6:]
    # get timestamp corresponding to time 0:00:00
    first_daily_timestamp = utime.mktime(date)
    # calculate correction of the midnight timestamp to the origiral
    correction = timestamp - first_daily_timestamp

    return date, correction


def format_timestamp_to_human(timestamp: int) -> str:
    """
    Returns human-friendly representation of a unix timestamp (in seconds format).
    Minutes and seconds are always displayed as 2 digits.
    Example:
    >>> format_timestamp_to_human(0)
    '1970-01-01 00:00:00'
    >>> format_timestamp_to_human(1616051824)
    '2021-03-18 07:17:04'
    """
    date, correction = _calculate_timestamp_correction(timestamp)
    # negative correction = substract 12 hours and calculate again
    if correction < 0:
        date, correction = _calculate_timestamp_correction(timestamp - 43_200)
        correction += 43_200
    # create precise datetime by adding the correction datetime to date
    correction_tuple = utime.localtime(correction)
    precise_datetime = date[:3] + correction_tuple[3:6]

    return "{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        precise_datetime[0],  # year
        precise_datetime[1],  # month
        precise_datetime[2],  # mday
        precise_datetime[3],  # hour
        precise_datetime[4],  # minute
        precise_datetime[5],  # second
    )
