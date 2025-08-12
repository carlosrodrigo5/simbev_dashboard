FROM python:3.11-slim

WORKDIR /simbev_dashboard

# Install dependencies
COPY requirements.txt /simbev_dashboard
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY dashboard.py /simbev_dashboard/dashboard.py
COPY data /simbev_dashboard/data




# Expose port
EXPOSE 5006

# Run panel app
CMD ["panel", "serve", "dashboard.py", "--address", "0.0.0.0", "--port", "5006", "--allow-websocket-origin", "*"]
