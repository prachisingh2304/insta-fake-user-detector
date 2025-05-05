import streamlit as st
from instagrapi import Client
import os
import json
import pandas as pd

# ---------- CONFIGURATION ----------
NUM_USERS_TO_CHECK_DEFAULT = 5
# -----------------------------------

# Fake user detection logic
def is_fake_user(posts, followers, following, bio, username):
    suspicious_score = 0
    if posts == 0:
        suspicious_score += 2
    if followers <= 10:
        suspicious_score += 1
    if followers > 0 and (following / followers) > 5:
        suspicious_score += 2
    if followers == 0 and following >= 10:
        suspicious_score += 2
    spam_keywords = ['bitcoin', 'forex', 'follow back', 'promo', 'dm', 'cashapp']
    if bio:
        if any(keyword in bio.lower() for keyword in spam_keywords):
            suspicious_score += 2
        elif len(bio.strip()) < 10:
            suspicious_score += 1
    digits = sum(c.isdigit() for c in username)
    if digits > 4 or username.lower().startswith("user") or "insta" in username.lower():
        suspicious_score += 2
    if posts <= 1 and followers <= 5 and following >= 50:
        suspicious_score += 2
    if posts == 0 and followers <= 5 and "motivated" in bio.lower():
        suspicious_score += 2
    return suspicious_score >= 4

# Analyze individual user
def analyze_user(user):
    try:
        username = user.username
        posts = user.media_count
        followers = user.follower_count
        following = user.following_count
        bio = user.biography or "No bio"
        fake_status = "Yes" if is_fake_user(posts, followers, following, bio, username) else "No"
        return {
            "Username": username,
            "Posts": posts,
            "Followers": followers,
            "Following": following,
            "Bio": bio,
            "Fake Account": fake_status
        }
    except Exception as e:
        return {
            "Username": getattr(user, 'username', 'unknown'),
            "Error": str(e),
            "Fake Account": "Error"
        }

# Streamlit App
def app():
    st.title("🤖 Instagram Fake User Detector")

    username_input = st.text_input("Instagram Username")
    password_input = st.text_input("Instagram Password", type="password")
    post_url = st.text_input("Enter Instagram Post URL:")
    num_users_to_check = st.number_input("Number of Users to Check:", min_value=1, max_value=20, value=NUM_USERS_TO_CHECK_DEFAULT)

    if st.button("Start Analysis"):
        if not username_input or not password_input or not post_url:
            st.error("❗ Please fill in all fields.")
            return

        try:
            st.write("🔐 Logging in...")
            cl = Client()
            if os.path.exists("settings.json"):
                cl.load_settings("settings.json")
                cl.login(username_input, password_input)
            else:
                cl.login(username_input, password_input)
                cl.dump_settings("settings.json")

            media_pk = cl.media_pk_from_url(post_url)
            st.write("🔍 Getting likers...")
            likers = cl.media_likers(media_pk)

            user_data_list = []
            for user_short in likers[:num_users_to_check]:
                full_user = cl.user_info(user_short.pk)
                user_data = analyze_user(full_user)
                user_data_list.append(user_data)

            df = pd.DataFrame(user_data_list)
            st.subheader("📊 Results")
            st.dataframe(df)

            # Save to JSON
            json_data = json.dumps(user_data_list, indent=4, ensure_ascii=False)
            with open("instagram_users_report.json", "w", encoding="utf-8") as json_file:
                json_file.write(json_data)

            # Provide download button
            st.download_button(
                label="📥 Download Report as JSON",
                data=json_data,
                file_name="instagram_users_report.json",
                mime="application/json"
            )

            

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    app()
