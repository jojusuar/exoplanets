# NOMBRE
#### FrontEnd Repo: https://jonthz.github.io/CelestiaWeb/

## Overview
This project provides a pipeline for training a binary classification model, predicting if exoplanet candidates will be confirmed or are false positives, and generating a catalog of the predicted exoplanets for visualization in the Celestia Project 3D star visualizer. 

## Features
1. **Model training **:
   - Uses most recent dataset from the Kepler and Tess mission as the primary dataset for exoplanet information.
   - Trains a binary classification model for predicting if exoplanet candidates will be confirmed or are false positives.

2. **Inference**:
   - Uses the trained model to predict the classification for exoplanet candidates.
   
3. **Celestia catalog generator**:
   - Consumes the generated predictions to populate a planet catalog for 3D visualization using Celestia Project's software.
