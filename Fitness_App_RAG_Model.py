import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from ai71 import AI71
import time

AI71_API_KEY = "Enter your own (AI71_API_KEY) key to test the application" 
ai71 = AI71(AI71_API_KEY)

def collect_user_data():
    st.sidebar.header("Your Information")
    age = st.sidebar.number_input("Enter your age:", min_value=10, max_value=100, value=25)
    height = st.sidebar.number_input("Enter your height (in cm):", min_value=100, max_value=250, value=170)
    weight = st.sidebar.number_input("Enter your weight (in kg):", min_value=30, max_value=200, value=70)
    gender = st.sidebar.selectbox("Select your gender:", ["Male", "Female", "Other"])
    activity_level = st.sidebar.selectbox("Select your activity level:", ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"])
    goal = st.sidebar.selectbox("Select your fitness goal:", ["Weight Loss", "Muscle Gain", "Maintenance", "Improve Stamina"])

    # --- Additional Features ---
    st.sidebar.subheader("Dietary Preferences (Optional)")
    vegetarian = st.sidebar.checkbox("Vegetarian")
    vegan = st.sidebar.checkbox("Vegan")
    allergies = st.sidebar.text_input("Allergies (comma-separated, e.g., peanuts, dairy):")

    st.sidebar.subheader("Workout Preferences (Optional)")
    workout_days = st.sidebar.slider("How many days a week do you want to work out?", 1, 7, 4)
    workout_duration = st.sidebar.slider("Average workout duration (in minutes):", 30, 90, 45)

    return {
        "age": age, "height": height, "weight": weight, "gender": gender, 
        "activity_level": activity_level, "goal": goal, 
        "vegetarian": vegetarian, "vegan": vegan, "allergies": allergies,
        "workout_days": workout_days, "workout_duration": workout_duration
    }

def calculate_bmi(height, weight):
    bmi = weight / ((height / 100) ** 2)
    return bmi

def calculate_bmr(gender, weight, height, age):
    if gender == "Male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender == "Female":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age)  # Using male formula as default
    return bmr

def calculate_daily_calorie_needs(bmr, activity_level, goal):
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extra Active": 1.9
    }
    calorie_needs = bmr * activity_multipliers[activity_level]
    if goal == "Weight Loss":
        calorie_needs -= 500
    elif goal == "Muscle Gain":
        calorie_needs += 350  # Average between 250-500
    return int(calorie_needs)

def generate_meal_plan(calorie_goal, restrictions=""):
    prompt = f"""
    Generate a sample 7-day meal plan for a person with a daily calorie goal of {calorie_goal} calories. 
    The meal plan should include breakfast, lunch, dinner, and two snacks per day. 

    Dietary restrictions: {restrictions}

    Provide the meal plan in a clear and organized format, using bullet points for each day. 
    """
    response = ai71.chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    return response.choices[0].message.content

def generate_workout_plan(goal, days, duration, styles=""):
    prompt = f"""
    Create a sample weekly workout plan for someone aiming to {goal}, 
    who wants to work out {days} days a week, with each workout lasting 
    around {duration} minutes.

    Preferred workout styles: {styles}

    Include a variety of exercises targeting different muscle groups.
    Provide clear instructions for each exercise and day.  
    """
    response = ai71.chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    return response.choices[0].message.content

def get_ai_response(prompt, chat_history):
    messages = [{"role": "system", "content": "You are a helpful and knowledgeable fitness assistant."}]
    for turn in chat_history:
        messages.append({"role": "user", "content": turn[0]})
        messages.append({"role": "assistant", "content": turn[1]})
    messages.append({"role": "user", "content": prompt}) 

    try:
        completion = ai71.chat.completions.create(
            model="tiiuae/falcon-180b-chat",
            messages=messages,
            stream=False,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Streamlit App
st.title("FitGen - Your Personalized Fitness Guide")

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar
user_data = collect_user_data()
if st.sidebar.button("Generate Plan"):
    st.session_state.user_data = user_data

# Main Content Area
user_data = st.session_state.get("user_data", {})
if user_data:
    bmi = calculate_bmi(user_data["height"], user_data["weight"])
    bmr = calculate_bmr(user_data["gender"], user_data["weight"], user_data["height"], user_data["age"])
    daily_calories = calculate_daily_calorie_needs(bmr, user_data["activity_level"], user_data["goal"])

    st.header("Your Fitness Plan")
    st.write(f"**BMI:** {bmi:.2f}")
    st.write(f"**BMR:** {bmr:.2f} calories/day")
    st.write(f"**Daily Calorie Needs:** {daily_calories} calories/day")

    dietary_restrictions = ""
    if user_data["vegetarian"]:
        dietary_restrictions += "Vegetarian. "
    if user_data["vegan"]:
        dietary_restrictions += "Vegan. "
    if user_data["allergies"]:
        dietary_restrictions += f"Allergies: {user_data['allergies']}. " 

    st.subheader("Your Meal Plan")
    with st.spinner("Generating meal plan..."):
        time.sleep(1) # Simulate delay - remove in production
        meal_plan = generate_meal_plan(daily_calories, dietary_restrictions)
    st.write(meal_plan)

    st.subheader("Your Workout Plan")
    with st.spinner("Generating workout plan..."):
        time.sleep(1) # Simulate delay - remove in production
        workout_plan = generate_workout_plan(user_data["goal"], user_data["workout_days"], user_data["workout_duration"])
    st.write(workout_plan)

    st.subheader("Ask Your Fitness AI")
    user_question = st.text_input("Enter your fitness-related question:")
    if user_question:
        with st.spinner("Generating response..."):
            response = get_ai_response(user_question, st.session_state.chat_history)
            st.session_state.chat_history.append((user_question, response)) # Update history
            st.write(response)
    
    # Display chat history
    st.subheader("Chat History")
    for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
        st.write(f"**You:** {user_msg}")
        st.write(f"**Bot:** {bot_msg}") 
        if i < len(st.session_state.chat_history) - 1:
            st.markdown("---") 

else:
    st.write("Please fill in your information in the sidebar to generate your personalized fitness plan.")
