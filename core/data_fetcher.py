"""Data fetching module for NSE stocks using yfinance"""

import pandas as pd
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import time
import os
import streamlit as st

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    NSE_EQUITY_URL, MAX_WORKERS, DEFAULT_PERIOD,
    INDEX_NIFTY_50, INDEX_NIFTY_NEXT_50, INDEX_NIFTY_MIDCAP_150,
    INDEX_NIFTY_SMALLCAP_250, INDEX_NIFTY_MICROCAP_250,
    # Sectoral indices
    INDEX_NIFTY_AUTO, INDEX_NIFTY_BANK, INDEX_NIFTY_FINANCIAL,
    INDEX_NIFTY_FMCG, INDEX_NIFTY_IT, INDEX_NIFTY_METAL,
    INDEX_NIFTY_PHARMA, INDEX_NIFTY_PSU_BANK, INDEX_NIFTY_REALTY,
    INDEX_NIFTY_ENERGY, INDEX_NIFTY_INFRA, INDEX_NIFTY_MEDIA,
    INDEX_NIFTY_PRIVATE_BANK, INDEX_NIFTY_COMMODITIES, INDEX_NIFTY_CONSUMPTION,
    INDEX_NIFTY_OIL_GAS, INDEX_NIFTY_HEALTHCARE,
    # Thematic indices
    INDEX_NIFTY_CPSE, INDEX_NIFTY_GROWSECT15, INDEX_NIFTY_MNC,
    INDEX_NIFTY_PSE, INDEX_NIFTY_SERV_SECTOR
)


def get_nse_stock_list() -> pd.DataFrame:
    """
    Fetch list of all NSE-listed stocks.
    Returns DataFrame with symbol, company_name columns.
    """
    try:
        # Try to fetch from NSE archives
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(NSE_EQUITY_URL, headers=headers, timeout=10)

        if response.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            df = df[['SYMBOL', 'NAME OF COMPANY']].copy()
            df.columns = ['symbol', 'company_name']
            df['symbol'] = df['symbol'] + '.NS'
            return df
    except Exception as e:
        print(f"Error fetching NSE list: {e}")

    # Fallback: Use cached list or hardcoded popular stocks
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'nse_symbols.csv')
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path)

    # Ultimate fallback: Popular NSE stocks
    return get_nifty_stocks()


def get_nifty50_symbols() -> List[str]:
    """Get Nifty 50 stock symbols"""
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
        'TITAN.NS', 'BAJFINANCE.NS', 'WIPRO.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS',
        'HCLTECH.NS', 'TECHM.NS', 'POWERGRID.NS', 'NTPC.NS', 'TATAMOTORS.NS',
        'M&M.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS',
        'ADANIENT.NS', 'ADANIPORTS.NS', 'BPCL.NS', 'GRASIM.NS', 'DIVISLAB.NS',
        'DRREDDY.NS', 'CIPLA.NS', 'APOLLOHOSP.NS', 'EICHERMOT.NS', 'BRITANNIA.NS',
        'HEROMOTOCO.NS', 'BAJAJ-AUTO.NS', 'TATACONSUM.NS', 'HINDALCO.NS',
        'INDUSINDBK.NS', 'SBILIFE.NS', 'HDFCLIFE.NS', 'BAJAJFINSV.NS', 'UPL.NS', 'LTIM.NS'
    ]


def get_nifty100_symbols() -> List[str]:
    """Get Nifty 100 stock symbols (Nifty 50 + Next 50)"""
    nifty50 = get_nifty50_symbols()
    next50 = [
        'ABB.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS', 'AMBUJACEM.NS', 'AUROPHARMA.NS',
        'BAJAJHLDNG.NS', 'BANKBARODA.NS', 'BERGEPAINT.NS', 'BIOCON.NS', 'BOSCHLTD.NS',
        'CADILAHC.NS', 'CHOLAFIN.NS', 'COLPAL.NS', 'CONCOR.NS', 'DABUR.NS',
        'DLF.NS', 'GAIL.NS', 'GODREJCP.NS', 'HAVELLS.NS', 'HINDPETRO.NS',
        'ICICIPRULI.NS', 'ICICIGI.NS', 'INDUSTOWER.NS', 'IOC.NS', 'IRCTC.NS',
        'JINDALSTEL.NS', 'JUBLFOOD.NS', 'LUPIN.NS', 'MARICO.NS', 'MCDOWELL-N.NS',
        'MUTHOOTFIN.NS', 'NAUKRI.NS', 'NMDC.NS', 'OFSS.NS', 'PAGEIND.NS',
        'PEL.NS', 'PETRONET.NS', 'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS',
        'PNB.NS', 'RECLTD.NS', 'SBICARD.NS', 'SHREECEM.NS', 'SIEMENS.NS',
        'SRF.NS', 'TATAPOWER.NS', 'TORNTPHARM.NS', 'VEDL.NS', 'ZOMATO.NS'
    ]
    return nifty50 + next50


def get_nifty200_symbols() -> List[str]:
    """Get Nifty 200 stock symbols"""
    nifty100 = get_nifty100_symbols()
    additional = [
        'AARTIIND.NS', 'ACC.NS', 'ALKEM.NS', 'ASHOKLEY.NS', 'ASTRAL.NS',
        'ATUL.NS', 'AUBANK.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BATAINDIA.NS',
        'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'CANFINHOME.NS', 'CANBK.NS',
        'CGPOWER.NS', 'CHAMBLFERT.NS', 'COFORGE.NS', 'COROMANDEL.NS', 'CROMPTON.NS',
        'CUB.NS', 'CUMMINSIND.NS', 'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DIXON.NS',
        'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORTIS.NS', 'GLAND.NS',
        'GLAXO.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODREJPROP.NS', 'GRANULES.NS',
        'GSPL.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HDFCAMC.NS', 'HONAUT.NS',
        'IDFCFIRSTB.NS', 'IEX.NS', 'IIFL.NS', 'INDIANB.NS', 'INDHOTEL.NS',
        'INDIGO.NS', 'IPCALAB.NS', 'IRB.NS', 'IRFC.NS', 'IGL.NS',
        'JKCEMENT.NS', 'JSWENERGY.NS', 'KAJARIACER.NS', 'KEI.NS', 'L&TFH.NS',
        'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LTI.NS', 'LTTS.NS',
        'M&MFIN.NS', 'MANAPPURAM.NS', 'MAXHEALTH.NS', 'MCX.NS', 'METROPOLIS.NS',
        'MINDTREE.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS', 'NAM-INDIA.NS',
        'NATIONALUM.NS', 'NIACL.NS', 'OBEROIRLTY.NS', 'PERSISTENT.NS', 'POLYCAB.NS',
        'PRESTIGE.NS', 'PVRINOX.NS', 'RAIN.NS', 'RAMCOCEM.NS', 'RBLBANK.NS',
        'RELAXO.NS', 'SAIL.NS', 'SANOFI.NS', 'SCHAEFFLER.NS', 'SONACOMS.NS',
        'STARHEALTH.NS', 'SUNTV.NS', 'SUPREMEIND.NS', 'SYNGENE.NS', 'TATACHEM.NS',
        'TATACOMM.NS', 'TATAELXSI.NS', 'TRENT.NS', 'TRIDENT.NS', 'TVSMOTOR.NS',
        'UBL.NS', 'UNIONBANK.NS', 'VBL.NS', 'VOLTAS.NS', 'ZYDUSLIFE.NS'
    ]
    return nifty100 + additional


def get_nifty_next50_symbols() -> List[str]:
    """Get Nifty Next 50 stock symbols (separate from Nifty 50)"""
    return [
        'ABB.NS', 'ADANIGREEN.NS', 'ADANIPOWER.NS', 'AMBUJACEM.NS', 'AUROPHARMA.NS',
        'BAJAJHLDNG.NS', 'BANKBARODA.NS', 'BERGEPAINT.NS', 'BIOCON.NS', 'BOSCHLTD.NS',
        'CADILAHC.NS', 'CHOLAFIN.NS', 'COLPAL.NS', 'CONCOR.NS', 'DABUR.NS',
        'DLF.NS', 'GAIL.NS', 'GODREJCP.NS', 'HAVELLS.NS', 'HINDPETRO.NS',
        'ICICIPRULI.NS', 'ICICIGI.NS', 'INDUSTOWER.NS', 'IOC.NS', 'IRCTC.NS',
        'JINDALSTEL.NS', 'JUBLFOOD.NS', 'LUPIN.NS', 'MARICO.NS', 'MCDOWELL-N.NS',
        'MUTHOOTFIN.NS', 'NAUKRI.NS', 'NMDC.NS', 'OFSS.NS', 'PAGEIND.NS',
        'PEL.NS', 'PETRONET.NS', 'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS',
        'PNB.NS', 'RECLTD.NS', 'SBICARD.NS', 'SHREECEM.NS', 'SIEMENS.NS',
        'SRF.NS', 'TATAPOWER.NS', 'TORNTPHARM.NS', 'VEDL.NS', 'ZOMATO.NS'
    ]


def get_nifty_midcap150_symbols() -> List[str]:
    """Get Nifty Midcap 150 stock symbols"""
    return [
        'AARTIIND.NS', 'ACC.NS', 'AIAENG.NS', 'AJANTPHARM.NS', 'ALKEM.NS',
        'ALKYLAMINE.NS', 'AMARAJABAT.NS', 'APLAPOLLO.NS', 'ASHOKLEY.NS', 'ASTRAL.NS',
        'ATUL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'BALRAMCHIN.NS', 'BALKRISIND.NS',
        'BANDHANBNK.NS', 'BATAINDIA.NS', 'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS',
        'BLUEDART.NS', 'BRIGADE.NS', 'BSE.NS', 'CANFINHOME.NS', 'CARBORUNIV.NS',
        'CASTROLIND.NS', 'CDSL.NS', 'CENTURYTEX.NS', 'CESC.NS', 'CGPOWER.NS',
        'CHAMBLFERT.NS', 'CLEAN.NS', 'COFORGE.NS', 'COROMANDEL.NS', 'CREDITACC.NS',
        'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 'CYIENT.NS', 'DCMSHRIRAM.NS',
        'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DEVYANI.NS', 'DIXON.NS', 'EDELWEISS.NS',
        'EMAMILTD.NS', 'ENDURANCE.NS', 'ENGINERSIN.NS', 'EQUITAS.NS', 'ERIS.NS',
        'ESCORTS.NS', 'EXIDEIND.NS', 'FINCABLES.NS', 'FINEORG.NS', 'FSL.NS',
        'GAIL.NS', 'GLAND.NS', 'GLAXO.NS', 'GLENMARK.NS', 'GMRINFRA.NS',
        'GNFC.NS', 'GODFRYPHLP.NS', 'GODREJIND.NS', 'GODREJPROP.NS', 'GRINDWELL.NS',
        'GUJGASLTD.NS', 'HAL.NS', 'HAPPSTMNDS.NS', 'HATSUN.NS', 'HDFCAMC.NS',
        'HINDPETRO.NS', 'HONAUT.NS', 'HUDCO.NS', 'IDFCFIRSTB.NS', 'IEX.NS',
        'IIFL.NS', 'INDIANB.NS', 'INDHOTEL.NS', 'INDIAMART.NS', 'INDUSTOWER.NS',
        'INTELLECT.NS', 'IOB.NS', 'IOC.NS', 'IPCALAB.NS', 'IRB.NS',
        'IRFC.NS', 'IGL.NS', 'ISEC.NS', 'JBCHEPHARM.NS', 'JINDALSAW.NS',
        'JKCEMENT.NS', 'JKLAKSHMI.NS', 'JSWENERGY.NS', 'JTEKTINDIA.NS', 'JUBLFOOD.NS',
        'KAJARIACER.NS', 'KALPATPOWR.NS', 'KALYANKJIL.NS', 'KANSAINER.NS', 'KEC.NS',
        'KEI.NS', 'KIMS.NS', 'KPITTECH.NS', 'LALPATHLAB.NS', 'LATENTVIEW.NS',
        'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LINDEINDIA.NS', 'LTTS.NS', 'LUXIND.NS',
        'M&MFIN.NS', 'MANAPPURAM.NS', 'MAZDOCK.NS', 'METROPOLIS.NS', 'MFSL.NS',
        'MHRIL.NS', 'MIDHANI.NS', 'MMTC.NS', 'MOIL.NS', 'MOTHERSON.NS',
        'MPHASIS.NS', 'MRF.NS', 'MRPL.NS', 'NAM-INDIA.NS', 'NATCOPHARM.NS',
        'NATIONALUM.NS', 'NAVINFLUOR.NS', 'NBCC.NS', 'NCC.NS', 'NETWORK18.NS',
        'NH.NS', 'NLCINDIA.NS', 'OBEROIRLTY.NS', 'OIL.NS', 'OLECTRA.NS',
        'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS', 'PNB.NS', 'POLYCAB.NS',
        'POLYMED.NS', 'POONAWALLA.NS', 'PRESTIGE.NS', 'PRINCEPIPE.NS', 'PVRINOX.NS',
        'RADICO.NS', 'RAIN.NS', 'RAJESHEXPO.NS', 'RAMCOCEM.NS', 'RATNAMANI.NS',
        'RAYMOND.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RELAXO.NS', 'RVNL.NS',
        'SAIL.NS', 'SANOFI.NS', 'SCHAEFFLER.NS', 'SHRIRAMFIN.NS', 'SJVN.NS',
        'SKFINDIA.NS', 'SOBHA.NS', 'SONACOMS.NS', 'STARHEALTH.NS', 'SUMICHEM.NS',
        'SUNDRMFAST.NS', 'SUNTV.NS', 'SUPREMEIND.NS', 'SYNGENE.NS', 'TATACHEM.NS',
        'TATACOMM.NS', 'TATAELXSI.NS', 'THERMAX.NS', 'TIMKEN.NS', 'TORNTPOWER.NS',
        'TRIDENT.NS', 'TRITURBINE.NS', 'TVSMOTOR.NS', 'UBL.NS', 'UNIONBANK.NS',
        'UPL.NS', 'VBL.NS', 'VOLTAS.NS', 'VSTIND.NS', 'WELCORP.NS',
        'WHIRLPOOL.NS', 'ZEEL.NS', 'ZENSARTECH.NS', 'ZYDUSLIFE.NS'
    ]


def get_nifty_smallcap250_symbols() -> List[str]:
    """Get Nifty Smallcap 250 stock symbols"""
    return [
        '3MINDIA.NS', 'AAVAS.NS', 'AEGISCHEM.NS', 'AFFLE.NS', 'AKZOINDIA.NS',
        'ALLCARGO.NS', 'ANGELONE.NS', 'ANURAS.NS', 'APARINDS.NS', 'APTECHT.NS',
        'APTUS.NS', 'ARVINDFASN.NS', 'ASAHIINDIA.NS', 'ASTERDM.NS', 'ASTRAZEN.NS',
        'ATUL.NS', 'BANARISUG.NS', 'BASF.NS', 'BAYERCROP.NS', 'BEML.NS',
        'BIRLACORPN.NS', 'BLUESTARCO.NS', 'BLS.NS', 'BOROLTD.NS', 'BORORENEW.NS',
        'BSOFT.NS', 'CAMPUS.NS', 'CAMS.NS', 'CANBK.NS', 'CANFINHOME.NS',
        'CAPLIPOINT.NS', 'CARERATING.NS', 'CCL.NS', 'CEATLTD.NS', 'CENTRALBK.NS',
        'CENTURYPLY.NS', 'CHALET.NS', 'CHENNPETRO.NS', 'CHOICEIN.NS', 'CMSINFO.NS',
        'COCHINSHIP.NS', 'CONCORDBIO.NS', 'CRAFTSMAN.NS', 'CRISIL.NS', 'CYIENT.NS',
        'DATAPATTNS.NS', 'DCBBANK.NS', 'DCMSHRIRAM.NS', 'DELTACORP.NS', 'DHANI.NS',
        'DMART.NS', 'EASEMYTRIP.NS', 'ECLERX.NS', 'EDELWEISS.NS', 'EIDPARRY.NS',
        'ELECON.NS', 'ELGIEQUIP.NS', 'EMAMILTD.NS', 'EMIL.NS', 'ENGINERSIN.NS',
        'EPL.NS', 'EQUITAS.NS', 'ERIS.NS', 'FINCABLES.NS', 'FINPIPE.NS',
        'FLUOROCHEM.NS', 'GARFIBRES.NS', 'GATEWAY.NS', 'GENUSPOWER.NS', 'GHCL.NS',
        'GILLETTE.NS', 'GLAND.NS', 'GLENMARK.NS', 'GLOBUSSPR.NS', 'GMDCLTD.NS',
        'GMMPFAUDLR.NS', 'GODFRYPHLP.NS', 'GODREJAGRO.NS', 'GPIL.NS', 'GRAPHITE.NS',
        'GREAVESCOT.NS', 'GRINDWELL.NS', 'GRINFRA.NS', 'GSFC.NS', 'GSPL.NS',
        'GTLINFRA.NS', 'HAPPSTMNDS.NS', 'HATHWAY.NS', 'HATSUN.NS', 'HCC.NS',
        'HFCL.NS', 'HGS.NS', 'HIKAL.NS', 'HINDCOPPER.NS', 'HINDWARE.NS',
        'HLEGLAS.NS', 'HOMEFIRST.NS', 'HSCL.NS', 'HUDCO.NS', 'IDFC.NS',
        'IFBIND.NS', 'IIFLWAM.NS', 'IMAGICAA.NS', 'INDIASHLTR.NS', 'INDIACEM.NS',
        'INDIGOPNTS.NS', 'INDOCO.NS', 'INOXWIND.NS', 'INTELLECT.NS', 'IOB.NS',
        'IONEXCHANG.NS', 'ISEC.NS', 'ITI.NS', 'J&KBANK.NS', 'JAICORPLTD.NS',
        'JAMNAAUTO.NS', 'JAYNECOIND.NS', 'JBCHEPHARM.NS', 'JETAIRWAYS.NS', 'JINDALSAW.NS',
        'JKIL.NS', 'JKLAKSHMI.NS', 'JKPAPER.NS', 'JMFINANCIL.NS', 'JPASSOCIAT.NS',
        'JSL.NS', 'JSLHISAR.NS', 'JTEKTINDIA.NS', 'JUBLINGREA.NS', 'JUNIPER.NS',
        'JUSTDIAL.NS', 'JYOTHYLAB.NS', 'KABRAEXTRU.NS', 'KALYANKJIL.NS', 'KANSAINER.NS',
        'KARNA.NS', 'KECL.NS', 'KERNEX.NS', 'KSL.NS', 'LAOPALA.NS',
        'LATENTVIEW.NS', 'LEMONTREE.NS', 'LINDE.NS', 'LLOYDSME.NS', 'LUMAXIND.NS',
        'LUMAXTECH.NS', 'LUXIND.NS', 'MAHABANK.NS', 'MAHLIFE.NS', 'MAHLOG.NS',
        'MAHSEAMLES.NS', 'MAITHANALL.NS', 'MANINFRA.NS', 'MASFIN.NS', 'MAZDOCK.NS',
        'MAZDA.NS', 'METROPOLIS.NS', 'MFSL.NS', 'MHRIL.NS', 'MIDHANI.NS',
        'MINDACORP.NS', 'MMTC.NS', 'MOIL.NS', 'MOLDTKPAC.NS', 'MOREPENLAB.NS',
        'MOTILALOFS.NS', 'MPHASIS.NS', 'MRPL.NS', 'MSPL.NS', 'MUKANDLTD.NS',
        'NAM-INDIA.NS', 'NATCOPHARM.NS', 'NAVINFLUOR.NS', 'NAVNETEDUL.NS', 'NBCC.NS',
        'NCC.NS', 'NESTLEIND.NS', 'NETWORK18.NS', 'NFL.NS', 'NH.NS',
        'NIACL.NS', 'NLCINDIA.NS', 'NOCIL.NS', 'NRBBEARING.NS', 'NUCLEUS.NS',
        'OIL.NS', 'OLECTRA.NS', 'OMINFRAL.NS', 'ONMOBILE.NS', 'OPTIEMUS.NS',
        'ORCHPHARMA.NS', 'ORIENT.NS', 'ORIENTCEM.NS', 'ORIENTELEC.NS', 'PANAMAPET.NS',
        'PARAGMILK.NS', 'PCJEWELLER.NS', 'PDMJEPAPER.NS', 'PENIND.NS', 'PFIZER.NS',
        'PGHL.NS', 'PHOENIXLTD.NS', 'PILANIINVS.NS', 'PNBHOUSING.NS', 'POCL.NS',
        'POLYMED.NS', 'POONAWALLA.NS', 'POWERMECH.NS', 'PRECAM.NS', 'PRECWIRE.NS',
        'PREMEXPLN.NS', 'PRIMESECU.NS', 'PRINCEPIPE.NS', 'PRIVISCL.NS', 'PSPPROJECT.NS',
        'PTCIL.NS', 'QUESS.NS', 'RADICO.NS', 'RAGHAV.NS', 'RAJESHEXPO.NS',
        'RAJRATAN.NS', 'RAMKY.NS', 'RANEHOLDIN.NS', 'RATNAMANI.NS', 'RAYMOND.NS',
        'REDINGTON.NS', 'RELIGARE.NS', 'RESPONIND.NS', 'RITCO.NS', 'ROSSARI.NS',
        'ROUTE.NS', 'RPSGVENT.NS', 'RTNPOWER.NS', 'RVNL.NS', 'SADBHIN.NS',
        'SAGCEM.NS', 'SANDHAR.NS', 'SANOFI.NS', 'SARDAEN.NS', 'SAREGAMA.NS',
        'SATIN.NS', 'SEQUENT.NS', 'SHANKARA.NS', 'SHILCHAR.NS', 'SHOPERSTOP.NS',
        'SHYAMMETL.NS', 'SIS.NS', 'SJVN.NS', 'SKFINDIA.NS', 'SNOWMAN.NS',
        'SOBHA.NS', 'SOLARA.NS', 'SONATSOFTW.NS', 'SOUTHBANK.NS', 'SPARC.NS',
        'SPANDANA.NS', 'SPICEJET.NS', 'SSWL.NS', 'STAR.NS', 'SUDARSCHEM.NS'
    ]


def get_nifty_microcap250_symbols() -> List[str]:
    """Get Nifty Microcap 250 stock symbols"""
    return [
        '20MICRONS.NS', '21STCENMGM.NS', '5PAISA.NS', 'A2ZINFRA.NS', 'AAKASH.NS',
        'AARTIDRUGS.NS', 'ABAN.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ABSLAMC.NS',
        'ACCELYA.NS', 'ADVENZYMES.NS', 'AEGISCHEM.NS', 'AETHER.NS', 'AGCNET.NS',
        'AHLUCONT.NS', 'AIAENG.NS', 'AIFL.NS', 'AJMERA.NS', 'AKSHOPTFBR.NS',
        'ALEMBICLTD.NS', 'ALMONDZ.NS', 'ALPA.NS', 'ALPHAGEO.NS', 'AMARAJABAT.NS',
        'AMJLAND.NS', 'ANDREWYU.NS', 'ANGIND.NS', 'ANMOL.NS', 'ANTGRAPHIC.NS',
        'APCOTEXIND.NS', 'APEX.NS', 'APLAPOLLO.NS', 'APOLSINHOT.NS', 'ARCHIDPLY.NS',
        'ARIHANT.NS', 'ARIHANTSUP.NS', 'ARROWGREEN.NS', 'ARSHIYA.NS', 'ASAHISONG.NS',
        'ASHIANA.NS', 'ASHIMASYN.NS', 'ASIANTILES.NS', 'ASTEC.NS', 'ATFL.NS',
        'AURIONPRO.NS', 'AUTOMOTIVE.NS', 'AVANTI.NS', 'AVTNPL.NS', 'AXISCADES.NS',
        'AYMSYNTEX.NS', 'BAFNAPH.NS', 'BAJAJCON.NS', 'BAJAJHCARE.NS', 'BALMLAWRIE.NS',
        'BALPHARMA.NS', 'BALRAMCHIN.NS', 'BANCOINDIA.NS', 'BANG.NS', 'BANSWRAS.NS',
        'BARTRONICS.NS', 'BCG.NS', 'BECTORFOOD.NS', 'BEDMUTHA.NS', 'BEL.NS',
        'BEPL.NS', 'BERGEPAINT.NS', 'BHAGERIA.NS', 'BHANDARI.NS', 'BHARATGEAR.NS',
        'BHARATWIRE.NS', 'BIGBLOC.NS', 'BIOFILCHEM.NS', 'BIRLACABLE.NS', 'BKM.NS',
        'BLISSGVS.NS', 'BLUEDART.NS', 'BODALCHEM.NS', 'BOMDYEING.NS', 'BPCL.NS',
        'BRIGADE.NS', 'BROOKFIELD.NS', 'BSE.NS', 'BUTTERFLY.NS', 'CAMLINFINE.NS',
        'CANDC.NS', 'CAPACITE.NS', 'CAPTRUST.NS', 'CARBORUNIV.NS', 'CARERATING.NS',
        'CARYSIL.NS', 'CASTROLIND.NS', 'CCHHL.NS', 'CDSL.NS', 'CELEBRITY.NS',
        'CENTUM.NS', 'CENTURYTEX.NS', 'CERA.NS', 'CGVAK.NS', 'CHEMCON.NS',
        'CHEMFAB.NS', 'CHEMOPAP.NS', 'CHOLAHLDNG.NS', 'CIGNITI.NS', 'CINELINE.NS',
        'CINEVISTA.NS', 'CLEAN.NS', 'CLSEL.NS', 'COALINDIA.NS', 'CONFIPET.NS',
        'CONTROLPR.NS', 'CORALFINAC.NS', 'CREAMLINE.NS', 'CREDITACC.NS', 'CSBBANK.NS',
        'CTE.NS', 'CUPID.NS', 'CYBERTECH.NS', 'DALMIASUG.NS', 'DATAMATICS.NS',
        'DBCORP.NS', 'DBOL.NS', 'DCAL.NS', 'DCMFINSERV.NS', 'DEEPAKFERT.NS',
        'DENISCO.NS', 'DHARAMSI.NS', 'DHAMPURSUG.NS', 'DHANBANK.NS', 'DHANLAXMI.NS',
        'DHANUKA.NS', 'DHARANI.NS', 'DHUNSERI.NS', 'DIAMONDYD.NS', 'DIASORIN.NS',
        'DICIND.NS', 'DIGISPICE.NS', 'DINAMICTECH.NS', 'DIVYASHAKTI.NS', 'DLINKINDIA.NS',
        'DQE.NS', 'DREDGECORP.NS', 'DRSTONE.NS', 'DVL.NS', 'DWARKESH.NS',
        'DYNAMATECH.NS', 'DYNPRO.NS', 'EASEMYTRIP.NS', 'ECLERX.NS', 'EDELWEISS.NS',
        'EDUCOMP.NS', 'EIDPARRY.NS', 'EIHAHOTELS.NS', 'EIMCOELECO.NS', 'ELDEHSG.NS',
        'ELECON.NS', 'ELGIEQUIP.NS', 'ELGIRUBCO.NS', 'EMIL.NS', 'EMKAY.NS',
        'EMMBI.NS', 'ENDURANCE.NS', 'ENERGYDEV.NS', 'ENGINERSIN.NS', 'ENIL.NS',
        'EPL.NS', 'EQUITASBNK.NS', 'ERIS.NS', 'EROSMEDIA.NS', 'ESABINDIA.NS',
        'ESCORTS.NS', 'ESSARSHPNG.NS', 'ESSELPACK.NS', 'EVERESTIND.NS', 'EXCELCROP.NS',
        'EXCELINDUS.NS', 'EXIDEIND.NS', 'EXPLEOSOL.NS', 'FAIRCHEM.NS', 'FDC.NS',
        'FELDVR.NS', 'FIEM.NS', 'FILATEX.NS', 'FINCABLES.NS', 'FINOLEXIND.NS',
        'FINPIPE.NS', 'FLEXITUFF.NS', 'FLFL.NS', 'FMGOETZE.NS', 'FMNL.NS',
        'FORBESCO.NS', 'FORCEMOT.NS', 'FORTIS.NS', 'FOSECOIND.NS', 'FRETAIL.NS',
        'FSC.NS', 'FSL.NS', 'GABRIEL.NS', 'GALLANTT.NS', 'GANDHAR.NS',
        'GANDHITUBE.NS', 'GANESHHOUC.NS', 'GARFIBRES.NS', 'GATEWAY.NS', 'GAYAHWS.NS',
        'GDL.NS', 'GEECEE.NS', 'GENCON.NS', 'GENUSPOWER.NS', 'GEOJITFSL.NS',
        'GEPIL.NS', 'GHCL.NS', 'GICHSGFIN.NS', 'GICRE.NS', 'GILLETTE.NS'
    ]


# ========== SECTORAL INDEX SYMBOLS ==========

def get_nifty_auto_symbols() -> List[str]:
    """Get Nifty Auto index constituents"""
    return [
        'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS',
        'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'BALKRISIND.NS', 'BHARATFORG.NS',
        'BOSCHLTD.NS', 'MOTHERSON.NS', 'MRF.NS', 'EXIDEIND.NS', 'APOLLOTYRE.NS'
    ]


def get_nifty_bank_symbols() -> List[str]:
    """Get Nifty Bank index constituents"""
    return [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'INDUSINDBK.NS', 'BANDHANBNK.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS',
        'BANKBARODA.NS', 'AUBANK.NS'
    ]


def get_nifty_financial_symbols() -> List[str]:
    """Get Nifty Financial Services index constituents"""
    return [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIPRULI.NS',
        'ICICIGI.NS', 'CHOLAFIN.NS', 'MUTHOOTFIN.NS', 'SHRIRAMFIN.NS', 'PFC.NS',
        'RECLTD.NS', 'LICHSGFIN.NS', 'M&MFIN.NS', 'MANAPPURAM.NS', 'POONAWALLA.NS'
    ]


def get_nifty_fmcg_symbols() -> List[str]:
    """Get Nifty FMCG index constituents"""
    return [
        'HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'BRITANNIA.NS', 'TATACONSUM.NS',
        'DABUR.NS', 'GODREJCP.NS', 'MARICO.NS', 'COLPAL.NS', 'PGHH.NS',
        'EMAMILTD.NS', 'VBL.NS', 'UBL.NS', 'MCDOWELL-N.NS', 'RADICO.NS'
    ]


def get_nifty_it_symbols() -> List[str]:
    """Get Nifty IT index constituents"""
    return [
        'TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS',
        'LTIM.NS', 'MPHASIS.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'LTTS.NS'
    ]


def get_nifty_metal_symbols() -> List[str]:
    """Get Nifty Metal index constituents"""
    return [
        'TATASTEEL.NS', 'JSWSTEEL.NS', 'HINDALCO.NS', 'VEDL.NS', 'COALINDIA.NS',
        'SAIL.NS', 'NMDC.NS', 'NATIONALUM.NS', 'JINDALSTEL.NS', 'HINDZINC.NS',
        'APLAPOLLO.NS', 'RATNAMANI.NS', 'WELCORP.NS', 'MOIL.NS', 'HINDCOPPER.NS'
    ]


def get_nifty_pharma_symbols() -> List[str]:
    """Get Nifty Pharma index constituents"""
    return [
        'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS',
        'LUPIN.NS', 'AUROPHARMA.NS', 'BIOCON.NS', 'TORNTPHARM.NS', 'ALKEM.NS',
        'ZYDUSLIFE.NS', 'IPCALAB.NS', 'GLENMARK.NS', 'LAURUSLABS.NS', 'ABBOTINDIA.NS',
        'PFIZER.NS', 'SANOFI.NS', 'GLAND.NS', 'NATCOPHARM.NS', 'GRANULES.NS'
    ]


def get_nifty_psu_bank_symbols() -> List[str]:
    """Get Nifty PSU Bank index constituents"""
    return [
        'SBIN.NS', 'PNB.NS', 'BANKBARODA.NS', 'CANBK.NS', 'UNIONBANK.NS',
        'INDIANB.NS', 'IOB.NS', 'CENTRALBK.NS', 'BANKINDIA.NS', 'MAHABANK.NS',
        'UCOBANK.NS', 'PSB.NS'
    ]


def get_nifty_realty_symbols() -> List[str]:
    """Get Nifty Realty index constituents"""
    return [
        'DLF.NS', 'GODREJPROP.NS', 'OBEROIRLTY.NS', 'PHOENIXLTD.NS', 'PRESTIGE.NS',
        'BRIGADE.NS', 'LODHA.NS', 'SOBHA.NS', 'SUNTECK.NS', 'MAHLIFE.NS'
    ]


def get_nifty_energy_symbols() -> List[str]:
    """Get Nifty Energy index constituents"""
    return [
        'RELIANCE.NS', 'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'BPCL.NS',
        'IOC.NS', 'GAIL.NS', 'TATAPOWER.NS', 'ADANIGREEN.NS', 'ADANIENSOL.NS'
    ]


def get_nifty_infra_symbols() -> List[str]:
    """Get Nifty Infrastructure index constituents"""
    return [
        'LT.NS', 'ADANIPORTS.NS', 'NTPC.NS', 'POWERGRID.NS', 'ULTRACEMCO.NS',
        'GRASIM.NS', 'BHARTIARTL.NS', 'ADANIENT.NS', 'SIEMENS.NS', 'ABB.NS',
        'HAVELLS.NS', 'CUMMINSIND.NS', 'BHEL.NS', 'IRCTC.NS', 'GMRINFRA.NS',
        'IRB.NS', 'NCC.NS', 'NBCC.NS', 'SAIL.NS', 'NMDC.NS',
        'CONCOR.NS', 'APOLLOHOSP.NS', 'MAXHEALTH.NS', 'FORTIS.NS', 'ZOMATO.NS',
        'NYKAA.NS', 'PAYTM.NS', 'DELHIVERY.NS', 'RVNL.NS', 'IRFC.NS'
    ]


def get_nifty_media_symbols() -> List[str]:
    """Get Nifty Media index constituents"""
    return [
        'ZEEL.NS', 'SUNTV.NS', 'PVR.NS', 'PVRINOX.NS', 'NETWORK18.NS',
        'TV18BRDCST.NS', 'DISHTV.NS', 'NAZARA.NS', 'SAREGAMA.NS', 'TIPS.NS'
    ]


def get_nifty_private_bank_symbols() -> List[str]:
    """Get Nifty Private Bank index constituents"""
    return [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'INDUSINDBK.NS',
        'BANDHANBNK.NS', 'FEDERALBNK.NS', 'IDFCFIRSTB.NS', 'RBLBANK.NS', 'AUBANK.NS'
    ]


def get_nifty_commodities_symbols() -> List[str]:
    """Get Nifty Commodities index constituents"""
    return [
        'RELIANCE.NS', 'ONGC.NS', 'TATASTEEL.NS', 'JSWSTEEL.NS', 'HINDALCO.NS',
        'VEDL.NS', 'COALINDIA.NS', 'GAIL.NS', 'BPCL.NS', 'IOC.NS',
        'NTPC.NS', 'NMDC.NS', 'SAIL.NS', 'JINDALSTEL.NS', 'TATAPOWER.NS',
        'UPL.NS', 'PIDILITIND.NS', 'SRF.NS', 'ATUL.NS', 'DEEPAKNTR.NS',
        'GRASIM.NS', 'ULTRACEMCO.NS', 'AMBUJACEM.NS', 'SHREECEM.NS', 'ACC.NS',
        'RAMCOCEM.NS', 'DALBHARAT.NS', 'JKCEMENT.NS', 'BIRLASOFT.NS', 'IGL.NS'
    ]


def get_nifty_consumption_symbols() -> List[str]:
    """Get Nifty Consumption index constituents"""
    return [
        'HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS', 'TITAN.NS', 'TRENT.NS',
        'BRITANNIA.NS', 'TATACONSUM.NS', 'DABUR.NS', 'GODREJCP.NS', 'MARICO.NS',
        'COLPAL.NS', 'PIDILITIND.NS', 'PAGEIND.NS', 'VOLTAS.NS', 'HAVELLS.NS',
        'CROMPTON.NS', 'WHIRLPOOL.NS', 'BLUESTARCO.NS', 'BATAINDIA.NS', 'RELAXO.NS',
        'VMART.NS', 'TATAELXSI.NS', 'INDIGO.NS', 'MARUTI.NS', 'HEROMOTOCO.NS',
        'BAJAJ-AUTO.NS', 'EICHERMOT.NS', 'ASIANPAINT.NS', 'BERGEPAINT.NS', 'KANSAINER.NS'
    ]


def get_nifty_oil_gas_symbols() -> List[str]:
    """Get Nifty Oil & Gas index constituents"""
    return [
        'RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'IOC.NS', 'GAIL.NS',
        'HINDPETRO.NS', 'PETRONET.NS', 'OIL.NS', 'MRPL.NS', 'CHENNPETRO.NS',
        'IGL.NS', 'MGL.NS', 'GUJGASLTD.NS', 'ATGL.NS', 'GSPL.NS'
    ]


def get_nifty_healthcare_symbols() -> List[str]:
    """Get Nifty Healthcare index constituents"""
    return [
        'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS', 'APOLLOHOSP.NS',
        'LUPIN.NS', 'AUROPHARMA.NS', 'BIOCON.NS', 'TORNTPHARM.NS', 'ALKEM.NS',
        'ZYDUSLIFE.NS', 'MAXHEALTH.NS', 'FORTIS.NS', 'LALPATHLAB.NS', 'METROPOLIS.NS',
        'SYNGENE.NS', 'AARTIDRUGS.NS', 'GLAND.NS', 'NATCOPHARM.NS', 'GRANULES.NS'
    ]


# ========== THEMATIC INDEX SYMBOLS ==========

def get_nifty_cpse_symbols() -> List[str]:
    """Get Nifty CPSE index constituents"""
    return [
        'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'COALINDIA.NS', 'IOC.NS',
        'BPCL.NS', 'GAIL.NS', 'BHEL.NS', 'RECLTD.NS', 'PFC.NS',
        'NHPC.NS', 'SJVN.NS'
    ]


def get_nifty_growsect15_symbols() -> List[str]:
    """Get Nifty Growsect 15 index constituents"""
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'BAJFINANCE.NS', 'MARUTI.NS'
    ]


def get_nifty_mnc_symbols() -> List[str]:
    """Get Nifty MNC index constituents"""
    return [
        'HINDUNILVR.NS', 'NESTLEIND.NS', 'MARUTI.NS', 'COLPAL.NS', 'ABBOTINDIA.NS',
        'SIEMENS.NS', 'ABB.NS', 'HONAUT.NS', 'BOSCHLTD.NS', 'PFIZER.NS',
        'GLAXO.NS', 'GILLETTE.NS', 'PGHH.NS', 'SANOFI.NS', 'CUMMINSIND.NS',
        'SCHAEFFLER.NS', 'SKFINDIA.NS', 'WHIRLPOOL.NS', 'TIMKEN.NS', 'GRINDWELL.NS',
        '3MINDIA.NS', 'AKZOINDIA.NS', 'CASTROLIND.NS', 'MPHASIS.NS', 'KALYANKJIL.NS',
        'LINDEINDIA.NS', 'NAVINFLUOR.NS', 'FIVESTAR.NS', 'TIINDIA.NS', 'BLUESTARCO.NS'
    ]


def get_nifty_pse_symbols() -> List[str]:
    """Get Nifty PSE index constituents"""
    return [
        'ONGC.NS', 'NTPC.NS', 'POWERGRID.NS', 'COALINDIA.NS', 'SBIN.NS',
        'IOC.NS', 'BPCL.NS', 'GAIL.NS', 'PNB.NS', 'BANKBARODA.NS',
        'BHEL.NS', 'RECLTD.NS', 'PFC.NS', 'NHPC.NS', 'NMDC.NS',
        'SAIL.NS', 'IRCTC.NS', 'CONCOR.NS', 'IRFC.NS', 'RVNL.NS'
    ]


def get_nifty_serv_sector_symbols() -> List[str]:
    """Get Nifty Services Sector index constituents"""
    return [
        'TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS',
        'BHARTIARTL.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'BAJFINANCE.NS', 'LT.NS', 'ADANIPORTS.NS', 'INDIGO.NS',
        'IRCTC.NS', 'ZOMATO.NS', 'NYKAA.NS', 'PAYTM.NS', 'DELHIVERY.NS',
        'LTIM.NS', 'MPHASIS.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'LTTS.NS',
        'APOLLOHOSP.NS', 'MAXHEALTH.NS', 'FORTIS.NS', 'LALPATHLAB.NS', 'METROPOLIS.NS'
    ]


def get_symbols_by_index(index_name: str) -> List[str]:
    """
    Get stock symbols for a given index name.

    Args:
        index_name: One of INDEX_NIFTY_50, INDEX_NIFTY_NEXT_50, etc.

    Returns:
        List of stock symbols
    """
    index_map = {
        # Broad Market Indices
        INDEX_NIFTY_50: get_nifty50_symbols,
        INDEX_NIFTY_NEXT_50: get_nifty_next50_symbols,
        INDEX_NIFTY_MIDCAP_150: get_nifty_midcap150_symbols,
        INDEX_NIFTY_SMALLCAP_250: get_nifty_smallcap250_symbols,
        INDEX_NIFTY_MICROCAP_250: get_nifty_microcap250_symbols,
        # Sectoral Indices
        INDEX_NIFTY_AUTO: get_nifty_auto_symbols,
        INDEX_NIFTY_BANK: get_nifty_bank_symbols,
        INDEX_NIFTY_FINANCIAL: get_nifty_financial_symbols,
        INDEX_NIFTY_FMCG: get_nifty_fmcg_symbols,
        INDEX_NIFTY_IT: get_nifty_it_symbols,
        INDEX_NIFTY_METAL: get_nifty_metal_symbols,
        INDEX_NIFTY_PHARMA: get_nifty_pharma_symbols,
        INDEX_NIFTY_PSU_BANK: get_nifty_psu_bank_symbols,
        INDEX_NIFTY_REALTY: get_nifty_realty_symbols,
        INDEX_NIFTY_ENERGY: get_nifty_energy_symbols,
        INDEX_NIFTY_INFRA: get_nifty_infra_symbols,
        INDEX_NIFTY_MEDIA: get_nifty_media_symbols,
        INDEX_NIFTY_PRIVATE_BANK: get_nifty_private_bank_symbols,
        INDEX_NIFTY_COMMODITIES: get_nifty_commodities_symbols,
        INDEX_NIFTY_CONSUMPTION: get_nifty_consumption_symbols,
        INDEX_NIFTY_OIL_GAS: get_nifty_oil_gas_symbols,
        INDEX_NIFTY_HEALTHCARE: get_nifty_healthcare_symbols,
        # Thematic Indices
        INDEX_NIFTY_CPSE: get_nifty_cpse_symbols,
        INDEX_NIFTY_GROWSECT15: get_nifty_growsect15_symbols,
        INDEX_NIFTY_MNC: get_nifty_mnc_symbols,
        INDEX_NIFTY_PSE: get_nifty_pse_symbols,
        INDEX_NIFTY_SERV_SECTOR: get_nifty_serv_sector_symbols,
    }

    func = index_map.get(index_name)
    if func:
        return func()
    return []


def get_combined_symbols(selected_indices: List[str]) -> List[str]:
    """
    Get combined stock symbols from multiple selected indices.
    Removes duplicates while preserving order.

    Args:
        selected_indices: List of index names

    Returns:
        Combined list of unique stock symbols
    """
    seen = set()
    combined = []

    for index_name in selected_indices:
        symbols = get_symbols_by_index(index_name)
        for symbol in symbols:
            if symbol not in seen:
                seen.add(symbol)
                combined.append(symbol)

    return combined


def get_nifty_stocks() -> pd.DataFrame:
    """Get Nifty 50 stocks as fallback"""
    nifty_50 = [
        ('RELIANCE.NS', 'Reliance Industries'),
        ('TCS.NS', 'Tata Consultancy Services'),
        ('HDFCBANK.NS', 'HDFC Bank'),
        ('INFY.NS', 'Infosys'),
        ('ICICIBANK.NS', 'ICICI Bank'),
        ('HINDUNILVR.NS', 'Hindustan Unilever'),
        ('SBIN.NS', 'State Bank of India'),
        ('BHARTIARTL.NS', 'Bharti Airtel'),
        ('ITC.NS', 'ITC'),
        ('KOTAKBANK.NS', 'Kotak Mahindra Bank'),
        ('LT.NS', 'Larsen & Toubro'),
        ('AXISBANK.NS', 'Axis Bank'),
        ('ASIANPAINT.NS', 'Asian Paints'),
        ('MARUTI.NS', 'Maruti Suzuki'),
        ('SUNPHARMA.NS', 'Sun Pharma'),
        ('TITAN.NS', 'Titan Company'),
        ('BAJFINANCE.NS', 'Bajaj Finance'),
        ('WIPRO.NS', 'Wipro'),
        ('ULTRACEMCO.NS', 'UltraTech Cement'),
        ('NESTLEIND.NS', 'Nestle India'),
        ('HCLTECH.NS', 'HCL Technologies'),
        ('TECHM.NS', 'Tech Mahindra'),
        ('POWERGRID.NS', 'Power Grid'),
        ('NTPC.NS', 'NTPC'),
        ('TATAMOTORS.NS', 'Tata Motors'),
        ('M&M.NS', 'Mahindra & Mahindra'),
        ('ONGC.NS', 'ONGC'),
        ('COALINDIA.NS', 'Coal India'),
        ('JSWSTEEL.NS', 'JSW Steel'),
        ('TATASTEEL.NS', 'Tata Steel'),
        ('ADANIENT.NS', 'Adani Enterprises'),
        ('ADANIPORTS.NS', 'Adani Ports'),
        ('BPCL.NS', 'BPCL'),
        ('GRASIM.NS', 'Grasim Industries'),
        ('DIVISLAB.NS', 'Divis Labs'),
        ('DRREDDY.NS', 'Dr Reddys Labs'),
        ('CIPLA.NS', 'Cipla'),
        ('APOLLOHOSP.NS', 'Apollo Hospitals'),
        ('EICHERMOT.NS', 'Eicher Motors'),
        ('BRITANNIA.NS', 'Britannia'),
        ('HEROMOTOCO.NS', 'Hero MotoCorp'),
        ('BAJAJ-AUTO.NS', 'Bajaj Auto'),
        ('TATACONSUM.NS', 'Tata Consumer'),
        ('HINDALCO.NS', 'Hindalco'),
        ('INDUSINDBK.NS', 'IndusInd Bank'),
        ('SBILIFE.NS', 'SBI Life'),
        ('HDFCLIFE.NS', 'HDFC Life'),
        ('BAJAJFINSV.NS', 'Bajaj Finserv'),
        ('UPL.NS', 'UPL'),
        ('LTIM.NS', 'LTIMindtree'),
    ]
    return pd.DataFrame(nifty_50, columns=['symbol', 'company_name'])


def fetch_stock_data(symbol: str, period: str = DEFAULT_PERIOD) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a single stock using yfinance.

    Args:
        symbol: Stock symbol with .NS suffix
        period: Data period (e.g., '6mo', '1y')

    Returns:
        DataFrame with OHLCV data or None if failed
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)

        if df.empty:
            return None

        # Ensure column names are standardized
        df = df.reset_index()
        df.columns = [col if col == 'Date' else col.capitalize() if col.lower() in ['open', 'high', 'low', 'close', 'volume'] else col for col in df.columns]

        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def fetch_multiple_stocks(symbols: List[str], period: str = DEFAULT_PERIOD,
                         progress_callback=None) -> Dict[str, pd.DataFrame]:
    """
    Fetch data for multiple stocks in parallel.

    Args:
        symbols: List of stock symbols
        period: Data period
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary mapping symbol to DataFrame
    """
    results = {}
    total = len(symbols)
    completed = 0

    def fetch_with_retry(symbol: str, max_retries: int = 2) -> Tuple[str, Optional[pd.DataFrame]]:
        for attempt in range(max_retries):
            try:
                df = fetch_stock_data(symbol, period)
                return (symbol, df)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    return (symbol, None)
        return (symbol, None)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_with_retry, sym): sym for sym in symbols}

        for future in as_completed(futures):
            symbol, df = future.result()
            if df is not None:
                results[symbol] = df

            completed += 1
            if progress_callback:
                progress_callback(completed / total)

    return results


@st.cache_data(ttl=3600)
def get_cached_stock_list() -> pd.DataFrame:
    """Get cached NSE stock list (refreshes every hour)"""
    return get_nse_stock_list()


def save_stock_list_cache(df: pd.DataFrame):
    """Save stock list to cache file"""
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'nse_symbols.csv')
    df.to_csv(cache_path, index=False)
