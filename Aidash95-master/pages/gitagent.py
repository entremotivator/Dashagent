import streamlit as st
import zipfile
import os
import shutil
import tempfile
from git import Repo
import requests

st.set_page_config(page_title="Upload Folder to GitHub", layout="centered")
st.title("📁➡️📦 Upload Folder to GitHub Repo")

# --- Inputs ---
github_token = st.text_input("🔑 GitHub Personal Access Token", type="password")
github_username = st.text_input("👤 GitHub Username")
repo_name_raw = st.text_input("📘 New Repository Name")
uploaded_zip = st.file_uploader("📂 Upload a ZIP file of your folder", type="zip")

create_repo = st.button("🚀 Create GitHub Repo & Upload")

if create_repo:
    if not all([github_token, github_username, repo_name_raw, uploaded_zip]):
        st.warning("Please complete all fields and upload a ZIP file.")
    else:
        try:
            repo_name = repo_name_raw.strip().replace(" ", "-")

            # Step 1: Create GitHub repo
            headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github+json"}
            data = {"name": repo_name, "private": False}
            res = requests.post("https://api.github.com/user/repos", headers=headers, json=data)
            if res.status_code != 201:
                st.error(f"❌ GitHub repo creation failed: {res.json().get('message')}")
                st.stop()
            st.success("✅ GitHub repository created!")

            # Step 2: Extract ZIP to a single folder in temp
            tmpdir = tempfile.mkdtemp()
            repo_folder = os.path.join(tmpdir, repo_name)
            os.mkdir(repo_folder)

            zip_path = os.path.join(tmpdir, uploaded_zip.name)
            with open(zip_path, "wb") as f:
                f.write(uploaded_zip.getbuffer())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to temp
                for member in zip_ref.namelist():
                    # Safely extract: extract to repo_folder
                    zip_ref.extract(member, repo_folder)

            # The extracted content is now always in repo_folder, regardless of ZIP structure

            # Step 3: Init and push Git repo
            repo = Repo.init(repo_folder)
            repo.git.config('user.email', f'{github_username}@users.noreply.github.com')
            repo.git.config('user.name', github_username)
            repo.git.add(A=True)  # Add all files (alternative to repo.index.add)
            repo.index.commit("Initial commit")

            remote_url = f"https://{github_username}:{github_token}@github.com/{github_username}/{repo_name}.git"
            if "origin" not in [r.name for r in repo.remotes]:
                origin = repo.create_remote('origin', remote_url)
            else:
                origin = repo.remotes.origin
                origin.set_url(remote_url)

            origin.push(refspec='HEAD:refs/heads/master')
            st.success("🎉 Folder successfully pushed to GitHub!")
            st.markdown(f"[🌐 View on GitHub](https://github.com/{github_username}/{repo_name})")

        except Exception as e:
            st.error(f"❌ Error: {e}")
