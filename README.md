# API Backend for GPT-AQG Project

This repository contains the backend API for the GPT-AQG project. It allows generating templates and questions based on course content. The front-end team can use this API to test their UI and integrate it with the backend.

## Getting Started

### Prerequisites

Ensure you have the following software installed:
- Python 3.8+
- MySQL
- Virtualenv (optional but recommended)

### Installation

- pip install -r requirements.txt

### For table Creation in DB
Following are the commands to migrate:
`flask db init`: Initializes the migration environment. Need to fire only once.
`flask db migrate`: Generates a new migration script based on the changes detected in your models.
`flask db upgrade`: Applies the migration to your database .