"""Car makes, models, and year data for dropdown selection."""

CAR_CATALOG = {
    "Porsche": {
        "911": list(range(1997, 2027)),
        "Carrera": list(range(2000, 2027)),
        "Turbo": list(range(1993, 2027)),
        "911 RS": list(range(2010, 2027)),
        "930": list(range(1975, 1990)),
        "Boxster": list(range(1996, 2027)),
        "Cayman": list(range(2005, 2027)),
        "Cayenne": list(range(2002, 2027)),
        "Panamera": list(range(2009, 2027)),
        "Macan": list(range(2014, 2027)),
    },
    "Ferrari": {
        "F430": list(range(2004, 2010)),
        "F8 Tributo": list(range(2019, 2027)),
        "SF90 Stradale": list(range(2019, 2027)),
        "Roma": list(range(2020, 2027)),
        "296 GTB": list(range(2021, 2027)),
        "Testarossa": list(range(1984, 1992)),
        "F40": list(range(1987, 1992)),
        "F50": list(range(1995, 1998)),
    },
    "Lamborghini": {
        "Aventador": list(range(2011, 2022)),
        "Huracán": list(range(2014, 2027)),
        "Revuelto": list(range(2023, 2027)),
        "Countach": list(range(1974, 1990)),
        "Diablo": list(range(1990, 2001)),
        "Murciélago": list(range(2001, 2011)),
    },
    "BMW": {
        "M3": list(range(1987, 2027)),
        "M5": list(range(1985, 2027)),
        "M4": list(range(2014, 2027)),
        "Z3": list(range(1995, 2002)),
        "Z4": list(range(2002, 2027)),
        "i8": list(range(2014, 2022)),
        "3 Series": list(range(1975, 2027)),
        "5 Series": list(range(1972, 2027)),
    },
    "Mercedes-Benz": {
        "SL": list(range(1954, 2027)),
        "SLR": list(range(2003, 2009)),
        "AMG GT": list(range(2014, 2027)),
        "C63 AMG": list(range(2007, 2027)),
        "E63 AMG": list(range(2009, 2027)),
        "G-Class": list(range(1979, 2027)),
        "300 SL": list(range(1954, 1957)),
    },
    "Aston Martin": {
        "DB9": list(range(2004, 2012)),
        "DBS": list(range(2007, 2012)),
        "Vantage": list(range(2005, 2027)),
        "DB11": list(range(2016, 2020)),
        "DBS Superleggera": list(range(2018, 2027)),
        "DBX": list(range(2020, 2027)),
        "Rapide": list(range(2010, 2020)),
    },
    "Jaguar": {
        "E-Type": list(range(1961, 1975)),
        "XK": list(range(1996, 2014)),
        "XJ": list(range(1968, 2027)),
        "F-Type": list(range(2013, 2027)),
        "C-X75": list(range(2010, 2015)),
    },
    "Land Rover": {
        "Defender": list(range(1948, 2027)),
        "Range Rover": list(range(1970, 2027)),
        "Discovery": list(range(1989, 2027)),
        "Freelander": list(range(1997, 2014)),
        "Evoque": list(range(2011, 2027)),
    },
    "Audi": {
        "R8": list(range(2006, 2027)),
        "S4": list(range(1991, 2027)),
        "S5": list(range(2007, 2027)),
        "RS6": list(range(2002, 2027)),
        "TT": list(range(1998, 2027)),
        "A1": list(range(2010, 2027)),
    },
}


def get_makes() -> list[str]:
    """Get all available car makes."""
    return sorted(list(CAR_CATALOG.keys()))


def get_models(make: str) -> list[str]:
    """Get all available models for a given make."""
    make_key = next((k for k in CAR_CATALOG.keys() if k.lower() == make.lower()), None)
    if not make_key:
        return []
    return sorted(list(CAR_CATALOG[make_key].keys()))


def get_years(make: str, model: str) -> list[int]:
    """Get all available years for a given make and model."""
    make_key = next((k for k in CAR_CATALOG.keys() if k.lower() == make.lower()), None)
    if not make_key or model not in CAR_CATALOG[make_key]:
        return []
    return sorted(CAR_CATALOG[make_key][model])


def get_all_data() -> dict:
    """Get all makes, models, and years data."""
    return {
        make: {
            "models": {
                model: years
                for model, years in CAR_CATALOG[make].items()
            }
        }
        for make in CAR_CATALOG
    }
