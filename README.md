# OnlineShopAuth Service

---

## Overview

This repository hosts the **OnlineShopAuth** service, a core component of a microservice-oriented e-commerce platform. 
This service is responsible for handling user authentication and authorization, 
providing secure access to the system for both customers and administrators. 
It leverages **FastAPI** for its high performance and ease of use, **SQLAlchemy 2.0 (Async)** 
for asynchronous ORM operations with PostgreSQL, **Apache Kafka** for asynchronous communication, 
and **Redis** for caching or session management within the microservices ecosystem. 
A key security feature is the **use of RSA private keys for JWT signing**, 
with **public keys provided to other microservices for secure and efficient token verification**.

---

## Features

* **User Registration:** Securely register new user accounts.
* **User Authentication:** Authenticate users via email and password.
* **JWT Generation:** Issue JSON Web Tokens (JWT) for authenticated sessions.
* **Token Refresh:** Support for refreshing expired access tokens using refresh tokens.
* **Password Hashing:** Secure storage of user passwords using modern hashing algorithms.
* **Role-Based Authorization:** Basic support for user roles (e.g., `user`, `admin`).
* **Event-Driven Communication:** Publishes and consumes Kafka messages for user-related events.

---

## Tech Stack

* **FastAPI**: High-performance web framework for building APIs.
* **SQLAlchemy 2.0 (Async)**: Asynchronous ORM for database interactions.
* **PostgreSQL**: Relational database for storing user data.
* **Apache Kafka**: Distributed streaming platform for asynchronous communication.
* **Alembic**: Database migration tool.
* **Pydantic**: Data validation and settings management.
* **Passlib**: Secure password hashing.
* **PyJWT**: JWT (JSON Web Token) implementation.
* **Confluent-Kafka-Python**: Python client for Kafka.
* **Redis**: Asynchronous Redis client for Python.

---

