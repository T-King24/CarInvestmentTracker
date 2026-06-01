"""Auto Trader-style vehicle taxonomy: makes, models, variants and years.

This is reference taxonomy data (the list of makes/models/variants a user can
search for), not market metrics. It can be overridden by pointing
``CIT_CATALOG_API_URL`` at a live taxonomy feed; otherwise this curated catalog
mirrors the structure used by https://www.autotrader.co.uk/ search.

Each model maps to a metadata dict::

    {"years": [int, ...], "variants": [str, ...],
     "fuel": [str, ...], "transmission": [str, ...]}
"""

from __future__ import annotations

# Common drivetrain option sets reused across many models.
_AUTO = ["Automatic"]
_MANUAL = ["Manual"]
_BOTH = ["Manual", "Automatic"]
_PETROL = ["Petrol"]
_PETROL_HYBRID = ["Petrol", "Hybrid"]
_ALL_FUEL = ["Petrol", "Diesel", "Hybrid", "Electric"]


def _m(years, variants, fuel=None, transmission=None) -> dict:
    return {
        "years": list(years),
        "variants": list(variants),
        "fuel": list(fuel or _PETROL),
        "transmission": list(transmission or _BOTH),
    }


CAR_CATALOG: dict[str, dict[str, dict]] = {
    "Porsche": {
        "911": _m(range(1997, 2027), ["Carrera", "Carrera S", "Carrera 4S", "Targa", "Turbo", "Turbo S", "GT3", "GT3 RS", "GT2 RS"]),
        "718 Cayman": _m(range(2016, 2027), ["Cayman", "Cayman S", "Cayman GTS", "Cayman GT4"]),
        "718 Boxster": _m(range(2016, 2027), ["Boxster", "Boxster S", "Boxster GTS", "Boxster Spyder"]),
        "Boxster": _m(range(1996, 2016), ["Boxster", "Boxster S", "Boxster Spyder"]),
        "Cayman": _m(range(2005, 2016), ["Cayman", "Cayman S", "Cayman R"]),
        "Cayenne": _m(range(2002, 2027), ["Cayenne", "Cayenne S", "Cayenne GTS", "Cayenne Turbo"], _ALL_FUEL, _AUTO),
        "Panamera": _m(range(2009, 2027), ["Panamera", "Panamera 4S", "Panamera GTS", "Panamera Turbo"], _PETROL_HYBRID, _AUTO),
        "Macan": _m(range(2014, 2027), ["Macan", "Macan S", "Macan GTS", "Macan Turbo"], _ALL_FUEL, _AUTO),
        "Taycan": _m(range(2019, 2027), ["Taycan", "Taycan 4S", "Taycan GTS", "Taycan Turbo", "Taycan Turbo S"], ["Electric"], _AUTO),
        "930": _m(range(1975, 1990), ["Turbo"], _PETROL, _MANUAL),
    },
    "Ferrari": {
        "F430": _m(range(2004, 2010), ["F430", "F430 Spider", "430 Scuderia"], _PETROL, _BOTH),
        "458": _m(range(2009, 2016), ["458 Italia", "458 Spider", "458 Speciale"], _PETROL, _AUTO),
        "488": _m(range(2015, 2020), ["488 GTB", "488 Spider", "488 Pista"], _PETROL, _AUTO),
        "F8 Tributo": _m(range(2019, 2027), ["F8 Tributo", "F8 Spider"], _PETROL, _AUTO),
        "SF90 Stradale": _m(range(2019, 2027), ["SF90 Stradale", "SF90 Spider"], _PETROL_HYBRID, _AUTO),
        "Roma": _m(range(2020, 2027), ["Roma", "Roma Spider"], _PETROL, _AUTO),
        "296 GTB": _m(range(2021, 2027), ["296 GTB", "296 GTS"], _PETROL_HYBRID, _AUTO),
        "Testarossa": _m(range(1984, 1992), ["Testarossa", "512 TR"], _PETROL, _MANUAL),
        "F40": _m(range(1987, 1992), ["F40"], _PETROL, _MANUAL),
        "F50": _m(range(1995, 1998), ["F50"], _PETROL, _MANUAL),
    },
    "Lamborghini": {
        "Aventador": _m(range(2011, 2022), ["LP700-4", "S", "SV", "SVJ", "Ultimae"], _PETROL, _AUTO),
        "Huracan": _m(range(2014, 2027), ["LP610-4", "LP580-2", "EVO", "Performante", "STO", "Tecnica"], _PETROL, _AUTO),
        "Revuelto": _m(range(2023, 2027), ["Revuelto"], _PETROL_HYBRID, _AUTO),
        "Urus": _m(range(2018, 2027), ["Urus", "Urus S", "Urus Performante"], _PETROL, _AUTO),
        "Countach": _m(range(1974, 1990), ["LP400", "LP400S", "LP5000 QV", "25th Anniversary"], _PETROL, _MANUAL),
        "Diablo": _m(range(1990, 2001), ["Diablo", "VT", "SV", "GT"], _PETROL, _MANUAL),
        "Murcielago": _m(range(2001, 2011), ["Murcielago", "LP640", "LP670-4 SV"], _PETROL, _BOTH),
    },
    "BMW": {
        "M2": _m(range(2015, 2027), ["M2", "M2 Competition", "M2 CS"]),
        "M3": _m(range(1987, 2027), ["M3", "M3 Competition", "M3 CS", "M3 Touring"]),
        "M4": _m(range(2014, 2027), ["M4", "M4 Competition", "M4 CSL"]),
        "M5": _m(range(1985, 2027), ["M5", "M5 Competition", "M5 CS"]),
        "Z3": _m(range(1995, 2002), ["1.9", "2.8", "M Roadster"], _PETROL, _MANUAL),
        "Z4": _m(range(2002, 2027), ["sDrive20i", "sDrive30i", "M40i"]),
        "i8": _m(range(2014, 2022), ["Coupe", "Roadster"], _PETROL_HYBRID, _AUTO),
        "3 Series": _m(range(1990, 2027), ["320i", "330i", "330e", "M340i"], _ALL_FUEL, _BOTH),
        "5 Series": _m(range(1990, 2027), ["520i", "530i", "530e", "540i"], _ALL_FUEL, _AUTO),
    },
    "Mercedes-Benz": {
        "SL": _m(range(1989, 2027), ["SL 350", "SL 500", "SL 55 AMG", "SL 63 AMG"], _PETROL, _AUTO),
        "SLR": _m(range(2003, 2009), ["SLR McLaren", "722 Edition"], _PETROL, _AUTO),
        "AMG GT": _m(range(2014, 2027), ["GT", "GT S", "GT C", "GT R", "GT Black Series"], _PETROL, _AUTO),
        "C-Class": _m(range(2007, 2027), ["C 200", "C 300", "C 43 AMG", "C 63 AMG"], _ALL_FUEL, _AUTO),
        "E-Class": _m(range(2009, 2027), ["E 220", "E 300", "E 53 AMG", "E 63 AMG"], _ALL_FUEL, _AUTO),
        "G-Class": _m(range(1990, 2027), ["G 350d", "G 400d", "G 63 AMG"], ["Petrol", "Diesel"], _AUTO),
        "300 SL": _m(range(1954, 1957), ["Gullwing", "Roadster"], _PETROL, _MANUAL),
    },
    "Aston Martin": {
        "DB9": _m(range(2004, 2012), ["DB9", "DB9 Volante"], _PETROL, _AUTO),
        "DB11": _m(range(2016, 2024), ["V8", "V12", "AMR", "Volante"], _PETROL, _AUTO),
        "DB12": _m(range(2023, 2027), ["Coupe", "Volante"], _PETROL, _AUTO),
        "DBS": _m(range(2007, 2027), ["DBS", "DBS Superleggera", "DBS 770 Ultimate"], _PETROL, _AUTO),
        "Vantage": _m(range(2005, 2027), ["V8 Vantage", "V12 Vantage", "Vantage S", "Vantage AMR"], _PETROL, _BOTH),
        "DBX": _m(range(2020, 2027), ["DBX", "DBX707"], _PETROL, _AUTO),
        "Vanquish": _m(range(2001, 2018), ["Vanquish", "Vanquish S"], _PETROL, _AUTO),
    },
    "Jaguar": {
        "E-Type": _m(range(1961, 1975), ["Series 1", "Series 2", "Series 3"], _PETROL, _MANUAL),
        "F-Type": _m(range(2013, 2027), ["P300", "P450", "R", "SVR"], _PETROL, _BOTH),
        "XK": _m(range(1996, 2015), ["XK", "XKR", "XKR-S"], _PETROL, _AUTO),
        "XJ": _m(range(1990, 2019), ["XJ", "XJR", "XJ Supersport"], ["Petrol", "Diesel"], _AUTO),
        "XE": _m(range(2015, 2024), ["XE", "XE R-Dynamic", "XE Project 8"], _ALL_FUEL, _AUTO),
    },
    "Land Rover": {
        "Defender": _m(range(1990, 2027), ["90", "110", "130", "V8"], _ALL_FUEL, _BOTH),
        "Range Rover": _m(range(1990, 2027), ["Vogue", "Autobiography", "SVAutobiography"], _ALL_FUEL, _AUTO),
        "Range Rover Sport": _m(range(2005, 2027), ["SE", "HSE", "Autobiography", "SVR"], _ALL_FUEL, _AUTO),
        "Discovery": _m(range(1989, 2027), ["Discovery", "HSE", "Landmark"], ["Petrol", "Diesel"], _AUTO),
        "Evoque": _m(range(2011, 2027), ["S", "SE", "HSE", "Autobiography"], _ALL_FUEL, _AUTO),
    },
    "Audi": {
        "R8": _m(range(2006, 2027), ["V8", "V10", "V10 Plus", "V10 Performance"], _PETROL, _BOTH),
        "RS3": _m(range(2011, 2027), ["RS3 Sportback", "RS3 Saloon"], _PETROL, _AUTO),
        "RS4": _m(range(2000, 2027), ["RS4 Avant", "RS4 Saloon"], _PETROL, _AUTO),
        "RS6": _m(range(2002, 2027), ["RS6 Avant", "RS6 Performance"], _PETROL, _AUTO),
        "TT": _m(range(1998, 2024), ["TT", "TTS", "TT RS"]),
        "S4": _m(range(1991, 2027), ["S4 Saloon", "S4 Avant"]),
        "e-tron GT": _m(range(2021, 2027), ["e-tron GT", "RS e-tron GT"], ["Electric"], _AUTO),
    },
    "McLaren": {
        "570S": _m(range(2015, 2021), ["570S", "570GT", "570S Spider"], _PETROL, _AUTO),
        "720S": _m(range(2017, 2023), ["720S", "720S Spider"], _PETROL, _AUTO),
        "750S": _m(range(2023, 2027), ["750S", "750S Spider"], _PETROL, _AUTO),
        "Artura": _m(range(2021, 2027), ["Artura", "Artura Spider"], _PETROL_HYBRID, _AUTO),
        "P1": _m(range(2013, 2016), ["P1"], _PETROL_HYBRID, _AUTO),
    },
    "Lotus": {
        "Elise": _m(range(1996, 2022), ["S", "Sport 220", "Cup 250"], _PETROL, _MANUAL),
        "Exige": _m(range(2000, 2022), ["S", "Sport 350", "Sport 410", "Cup 430"], _PETROL, _MANUAL),
        "Evora": _m(range(2009, 2022), ["S", "400", "GT410", "GT430"], _PETROL, _BOTH),
        "Emira": _m(range(2022, 2027), ["First Edition", "Base", "V6"], _PETROL, _BOTH),
        "Evija": _m(range(2023, 2027), ["Evija"], ["Electric"], _AUTO),
    },
    "Toyota": {
        "GR Yaris": _m(range(2020, 2027), ["GR Yaris", "Circuit Pack", "GR4"], _PETROL, _MANUAL),
        "GR Supra": _m(range(2019, 2027), ["2.0", "3.0", "3.0 Pro"], _PETROL, _BOTH),
        "GR86": _m(range(2022, 2027), ["GR86"], _PETROL, _BOTH),
        "Supra (Mk4)": _m(range(1993, 2002), ["SZ", "RZ", "Turbo"], _PETROL, _BOTH),
    },
    "Nissan": {
        "GT-R": _m(range(2007, 2027), ["Pure", "Recaro", "Prestige", "Track Edition", "Nismo"], _PETROL, _AUTO),
        "370Z": _m(range(2009, 2021), ["370Z", "Nismo"], _PETROL, _BOTH),
        "Skyline GT-R": _m(range(1989, 2002), ["R32", "R33", "R34"], _PETROL, _MANUAL),
    },
    "Honda": {
        "Civic Type R": _m(range(2001, 2027), ["EP3", "FN2", "FK2", "FK8", "FL5"], _PETROL, _MANUAL),
        "NSX": _m(range(1990, 2005), ["NSX", "NSX-T", "NSX-R"], _PETROL, _BOTH),
        "S2000": _m(range(1999, 2009), ["S2000", "CR"], _PETROL, _MANUAL),
    },
}


def _make_key(make: str) -> str | None:
    return next((k for k in CAR_CATALOG if k.lower() == make.lower()), None)


def _model_key(make_key: str, model: str) -> str | None:
    models = CAR_CATALOG[make_key]
    return next((k for k in models if k.lower() == model.lower()), None)


def get_makes() -> list[str]:
    """Get all available car makes."""
    return sorted(CAR_CATALOG.keys())


def get_models(make: str) -> list[str]:
    """Get all available models for a given make."""
    make_key = _make_key(make)
    if not make_key:
        return []
    return sorted(CAR_CATALOG[make_key].keys())


def get_years(make: str, model: str) -> list[int]:
    """Get all available years for a given make and model."""
    make_key = _make_key(make)
    if not make_key:
        return []
    model_key = _model_key(make_key, model)
    if not model_key:
        return []
    return sorted(CAR_CATALOG[make_key][model_key]["years"])


def get_variants(make: str, model: str) -> list[str]:
    """Get all available variants/derivatives for a given make and model."""
    make_key = _make_key(make)
    if not make_key:
        return []
    model_key = _model_key(make_key, model)
    if not model_key:
        return []
    return list(CAR_CATALOG[make_key][model_key]["variants"])


def get_model_metadata(make: str, model: str) -> dict | None:
    """Return the full metadata dict (years, variants, fuel, transmission)."""
    make_key = _make_key(make)
    if not make_key:
        return None
    model_key = _model_key(make_key, model)
    if not model_key:
        return None
    return CAR_CATALOG[make_key][model_key]


def get_all_data() -> dict:
    """Get all makes, models, variants and years data."""
    return {
        make: {
            "models": {
                model: dict(meta)
                for model, meta in CAR_CATALOG[make].items()
            }
        }
        for make in CAR_CATALOG
    }
