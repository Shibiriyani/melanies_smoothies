
# Import python packages
import streamlit as st
import requests
import pandas as pd
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("""
Choose the fruits you want in your custom Smoothie!
""")

# Customer name
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit names and their API search values
my_dataframe = session.table(
    "smoothies.public.fruit_options"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)

# Convert Snowpark DataFrame to Pandas
pd_df = my_dataframe.to_pandas()

# st.dataframe(data=my_dataframe, use_container_width=True)
# st.dataframe(pd_df)

fruit_names = [
    row["FRUIT_NAME"]
    for row in my_dataframe.select("FRUIT_NAME").collect()
]

# Fruit selections
ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=fruit_names,
    max_selections=5,
    key="smoothie_fruits"
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Get the SEARCH_ON value for the selected fruit
        search_on = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ].iloc[0]

        st.write(
            "The search value for",
            fruit_chosen,
            "is",
            search_on,
            "."
        )

        # Display nutrition information
        st.subheader(fruit_chosen + ' Nutrition Information')

        # Use SEARCH_ON instead of FRUIT_NAME
        smoothiefroot_response = requests.get(
            f"https://my.smoothiefroot.com/api/fruit/{search_on}"
        )

        sf_df = st.dataframe(
            data=smoothiefroot_response.json(),
            use_container_width=True
        )

    # Create INSERT statement with both columns
    my_insert_stmt = """
    INSERT INTO smoothies.public.orders
    (ingredients, name_on_order)
    VALUES ('""" + ingredients_string + """', '""" + name_on_order.replace("'", "''") + """');
    """

    # Uncomment these lines to inspect SQL
    # st.write(my_insert_stmt)
    # st.stop()

    # Submit Order button
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        if not name_on_order.strip():
            st.warning("Please enter a name on your smoothie.")
        else:
            session.sql(my_insert_stmt).collect()
            st.success(
                f'Your Smoothie is ordered, {name_on_order}!',
                icon="✅"
            )
