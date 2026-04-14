# The LILA Game - Deployment Guide

A web-based wildlife camera trap identification game using real camera trap images from conservation research projects.

## Project Overview

This app provides an educational wildlife identification game where players view sequences of camera trap images and identify animals at various taxonomic levels. Players earn points based on the accuracy of their identification, from species (10 points) to family (3 points) to order (1 point).

**Tech Stack:**
- Backend: Flask with SQLite database
- Frontend: HTML/CSS/JavaScript (vanilla, no frameworks)
- LLM: Google Gemini API for hints and fun facts
- Deployment: Docker container with volume persistence
- Database: SQLite with camera trap image metadata

## Features

- **Real camera trap sequences** from wildlife research projects
- **Hierarchical scoring system** rewarding taxonomic accuracy
- **AI-powered hints** using Gemini API (without revealing answers)
- **Fun facts** about correctly identified animals
- **Autocomplete search** supporting scientific and common names
- **High score leaderboard** with persistent storage
- **Responsive interface** optimized for wildlife learning

## Project Structure


