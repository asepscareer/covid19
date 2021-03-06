import datetime
from functools import reduce
import streamlit as st
from PIL import Image
import pandas as pd
import altair as alt
import os
 

try:
    from app_secrets import MINIO_ACCESS_KEY, MINIO_ENCRYPT_KEY
except:
    access_key=os.getenv("MINIO_ACCESS_KEY")
    secret_key=os.getenv("MINIO_SECRET_KEY")

# Number from Google, you can pull requests for this (n/100k)
#southeastasia
inhabitants = {'Indonesia': 2677,
            'Brunei': 4.37479,
            'Malaysia': 325.159,
            'Cambodia': 170,
            'Singapore': 60,
            'Thailand': 700,
            'Vietnam': 970,
            "Laos": 70,
            'Burma': 550,
            'Philippines': 1100,
            'Timor-Leste': 13.20}
#south-asia
image = Image.open('maskeran.jpg')

@st.cache
def read_data():
    BASEURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series"    
    url_confirmed = f"{BASEURL}/time_series_covid19_confirmed_global.csv"
    url_deaths = f"{BASEURL}/time_series_covid19_deaths_global.csv"
    url_recovered = f"{BASEURL}/time_series_covid19_recovered_global.csv"

    confirmed = pd.read_csv(url_confirmed, index_col=0)
    deaths = pd.read_csv(url_deaths, index_col=0)
    recovered = pd.read_csv(url_recovered, index_col=0)

    # sum over potentially duplicate rows (France and their territories)
    confirmed = confirmed.groupby("Country/Region").sum().reset_index()
    deaths = deaths.groupby("Country/Region").sum().reset_index()
    recovered = recovered.groupby("Country/Region").sum().reset_index()


    return (confirmed, deaths, recovered)

def transform(df, collabel='confirmed'):
    dfm = pd.melt(df)
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["value"]]
    dfm.columns = [collabel]
    return dfm

def transform2(df, collabel='confirmed'):
    dfm = pd.melt(df, id_vars=["Country/Region"])
    dfm["date"] = pd.to_datetime(dfm.variable, infer_datetime_format=True)
    dfm = dfm.set_index("date")
    dfm = dfm[["Country/Region","value"]]
    dfm.columns = ["country", collabel]
    return dfm

def main():
    st.title("World-wide COVID-19 Outbreak Data Analysis")
    st.image(image, caption='-', use_column_width=True)
    st.markdown("""
    > COVID-19 is an infectious disease caused by a newly discovered type of coronavirus. The new virus and the disease it causes were not known before the outbreak in Wuhan, China, in December 2019.
    COVID-19 is now a pandemic occurring in many countries around the world.
    """)


    countries = ['Indonesia', 'Brunei','Malaysia','Cambodia','Singapore',
    'Thailand','Vietnam',"Laos", 'Burma', 'Philippines', 'Timor-Leste']

    analysis = st.sidebar.selectbox("Choose Analysis", ["Overview", "Country statistics", "Statistical comparison", "Data"])

    if analysis == "Overview":
        REGION = st.sidebar.radio("Select area", ('Southeast Asia', 'South Asia', 'East Asia', 'West Asia', 'Central Asia', 'North Asia',
        'Western Europe', 'Eastern Europe', 'Central Europe', 'Northern Europe', 'Southern Europe'))
        if REGION == 'Southeast Asia':
            st.header("COVID-19 cases and fatality rate on Southeast Asia")
            st.markdown("""\
                The data used are the reported case numbers of Southeast Asia countries"""
                f""" ({', '.join(countries)}). """
                """Based on existing data, the case fatality rate (CFR) is calculated as:  
                $$
                CFR[\%] = \\frac{fatalities}{\\textit{all cases}}
                $$
                """)
            st.warning("""
            You can select/ deselect countries and switch between linear and log scales.
            """)

            confirmed, deaths, recovered = read_data()

            multiselection = st.multiselect("Select countries:", countries, default=countries)
            logscale = st.checkbox("Log scale", False)

            confirmed = confirmed[confirmed["Country/Region"].isin(multiselection)]
            confirmed = confirmed.drop(["Lat", "Long"],axis=1)
            confirmed = transform2(confirmed, collabel="confirmed")

            deaths = deaths[deaths["Country/Region"].isin(multiselection)]
            deaths = deaths.drop(["Lat", "Long"],axis=1)
            deaths = transform2(deaths, collabel="deaths")

            frate = confirmed[["country"]]
            frate["frate"] = (deaths.deaths / confirmed.confirmed)*100

            # saveguard for empty selection 
            if len(multiselection) == 0:
                return 

            SCALE = alt.Scale(type='linear')
            if logscale:
                confirmed["confirmed"] += 0.00001

                confirmed = confirmed[confirmed.index > '2020-01-22']
                frate = frate[frate.index > '2020-01-22']
                
                SCALE = alt.Scale(type='log', domain=[10, int(max(confirmed.confirmed))], clamp=True)


            c2 = alt.Chart(confirmed.reset_index()).properties(height=150).mark_line().encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("confirmed:Q", title="Cases", scale=SCALE),
                color=alt.Color('country:N', title="Country")
            )

            # case fatality rate...
            c3 = alt.Chart(frate.reset_index()).properties(height=100).mark_line().encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("frate:Q", title="Fatality rate [%]", scale=alt.Scale(type='linear')),
                color=alt.Color('country:N', title="Country")
            )

            per100k = confirmed.loc[[confirmed.index.max()]].copy()
            per100k.loc[:,'inhabitants'] = per100k.apply(lambda x: inhabitants[x['country']], axis=1)
            per100k.loc[:,'per100k'] = per100k.confirmed / (per100k.inhabitants * 1_000_000) * 100_000
            per100k = per100k.set_index("country")
            per100k = per100k.sort_values(ascending=False, by='per100k')
            per100k.loc[:,'per100k'] = per100k.per100k.round(2)

            c4 = alt.Chart(per100k.reset_index()).properties(width=75).mark_bar().encode(
                x=alt.X("per100k:Q", title="Cases per 100k inhabitants"),
                y=alt.Y("country:N", title="Countries", sort=None),
                color=alt.Color('country:N', title="Country"),
                tooltip=[alt.Tooltip('country:N', title='Country'), 
                        alt.Tooltip('per100k:Q', title='Cases per 100k'),
                        alt.Tooltip('inhabitants:Q', title='Inhabitants (n/100k)')]
            )

            st.altair_chart(alt.hconcat(c4, alt.vconcat(c2, c3)), use_container_width=True)
        elif REGION == 'South Asia':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'North Asia':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'East Asia':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Central Asia':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'West Asia':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Western Europe':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Eastern Europe':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Central Europe':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Northern Europe':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')
        elif REGION == 'Southern Europe':
            st.info('Tampilkan Maps')
            st.warning('Data belum dimuat! Tampilkan seperti Asia Tenggara')

        st.markdown(f"""\
            <div style="font-size: small">
            ⚠️ Please take the CFR with a grain of salt. The ratio is 
            highly dependend on the total number of tests conducted in a country. In the early stages
            of the outbreak often mainly severe cases with clear symptoms are detected. Thus mild cases
            are not recorded which skews the CFR.
            </div><br/>

            """, unsafe_allow_html=True)

    elif analysis == "Data":

        confirmed, deaths, recovered = read_data()
        st.header("Global datasets")
        st.markdown("""\
            The reported number of confirmed (active), recovered and deceased COVID-19 cases per day. 
            """)

        #Data for confirmed cases
        #Rename for view Maps because on streamlit must 'latitude/lat' or 'longitude/long'
        st.subheader('Confirmed')
        st.dataframe(data=confirmed)
        st.subheader('Deaths')
        st.dataframe(data=deaths)
        st.subheader('Recovered')
        st.dataframe(data=recovered)
    elif analysis == 'Statistical comparison':
        st.warning("Tulis disini!")

    elif analysis == "Country statistics":        

        confirmed, deaths, recovered = read_data()
        
        st.header("Country statistics")
        st.markdown("""\
            The reported number of active, recovered and deceased COVID-19 cases by country """
            f""" (currently only {', '.join(confirmed['Country/Region'])}).  
            """
            """  
            ℹ️ You can select countries and plot data as cummulative counts or new active cases per day. 
            """)

        # selections
        selection = st.selectbox("Select country:", confirmed['Country/Region'])
        cummulative = st.radio("Display type:", ["total", "new cases"])
        #scaletransform = st.radio("Plot y-axis", ["linear", "pow"])
        
        confirmed = confirmed[confirmed["Country/Region"] == selection].iloc[:,3:]
        confirmed = transform(confirmed, collabel="confirmed")

        deaths = deaths[deaths["Country/Region"] == selection].iloc[:,3:]
        deaths = transform(deaths, collabel="deaths")

        recovered = recovered[recovered["Country/Region"] == selection].iloc[:,3:]
        recovered = transform(recovered, collabel="recovered")

        
        df = reduce(lambda a,b: pd.merge(a,b, on='date'), [confirmed, recovered, deaths])
        df["active"] = df.confirmed - (df.deaths + df.recovered)

        variables = ["recovered", "active", "deaths"]
        colors = ["steelblue", "orange", "black"]

        value_vars = variables
        SCALE = alt.Scale(domain=variables, range=colors)
        if cummulative == 'new cases':
            value_vars = ["new"]
            df["new"] = df.confirmed - df.shift(1).confirmed
            df["new"].loc[df.new < 0]  = 0
            SCALE = alt.Scale(domain=["new"], range=["orange"]) 

        dfm = pd.melt(df.reset_index(), id_vars=["date"], value_vars=value_vars)

        # introduce order col as altair does auto-sort on stacked elements
        dfm['order'] = dfm['variable'].replace(
            {val: i for i, val in enumerate(variables[::-1])}
        )

        c = alt.Chart(dfm.reset_index()).mark_bar().properties(height=200).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("sum(value):Q", title="Cases", scale=alt.Scale(type='linear')),
            color=alt.Color('variable:N', title="Category", scale=SCALE), #, sort=alt.EncodingSortField('value', order='ascending')),
            order='order'
        )

        if cummulative != 'new cases':
            st.altair_chart(c, use_container_width=True)
        else:
            # add smooth 7-day trend
            rm_7day = df[['new']].rolling('7D').mean().rename(columns={'new': 'value'})
            c_7day = alt.Chart(rm_7day.reset_index()).properties(height=200).mark_line(strokeDash=[1,1], color='red').encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("value:Q", title="Cases", scale=alt.Scale(type='linear')),
            )
            st.altair_chart((c + c_7day), use_container_width=True)
            st.markdown(f"""\
                <div style="font-size: small">Daily reported new cases (incl. 7-day average).</div><br/>
                """, unsafe_allow_html=True)
        pass
    # ----------------------
if __name__ == "__main__":
    main()