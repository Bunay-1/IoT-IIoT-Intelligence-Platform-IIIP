import asyncio
import json
import random
from datetime import datetime, timedelta

import asyncpg


async def generate_machine_data(conn):
    print("Generating machine data...")
    machines = [
        {
            "machine_id": "CNC-001",
            "name": "CNC Lathe 1",
            "location": "Factory A",
            "model": "XYZ-2000",
            "installation_date": "2022-01-15",
            "last_maintenance": "2024-11-01",
            "status": "operational",
            "metadata": {"manufacturer": "Acme Corp", "power_kw": 25},
        },
        {
            "machine_id": "CNC-002",
            "name": "CNC Mill 2",
            "location": "Factory B",
            "model": "XYZ-3000",
            "installation_date": "2021-06-20",
            "last_maintenance": "2024-10-15",
            "status": "maintenance",
            "metadata": {"manufacturer": "Globex Inc", "power_kw": 30},
        },
        {
            "machine_id": "CNC-003",
            "name": "CNC Router 3",
            "location": "Factory A",
            "model": "ABC-1000",
            "installation_date": "2023-03-10",
            "last_maintenance": "2024-12-01",
            "status": "idle",
            "metadata": {"manufacturer": "Innovate Ltd", "power_kw": 20},
        },
    ]

    for machine in machines:
        try:
            await conn.execute(
                """
                INSERT INTO machines (machine_id, name, location, model, installation_date, last_maintenance, status, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (machine_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    location = EXCLUDED.location,
                    model = EXCLUDED.model,
                    installation_date = EXCLUDED.installation_date,
                    last_maintenance = EXCLUDED.last_maintenance,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata
            """,
                machine["machine_id"],
                machine["name"],
                machine["location"],
                machine["model"],
                datetime.strptime(machine["installation_date"], "%Y-%m-%d").date(),
                datetime.strptime(machine["last_maintenance"], "%Y-%m-%d").date(),
                machine["status"],
                machine["metadata"],
            )
            print(f"Upserted machine: {machine['machine_id']}")
        except Exception as e:
            print(f"Error upserting machine {machine['machine_id']}: {e}")


async def generate_prediction_data(
    conn, machine_id, start_time, end_time, interval_minutes=15
):
    print(
        f"Generating prediction data for {machine_id} from {start_time} to {end_time}..."
    )
    current_time = start_time
    while current_time <= end_time:
        anomaly_score = round(random.uniform(0.01, 0.99), 2)
        failure_probability = round(random.uniform(0.001, 0.1), 3)
        remaining_useful_life = round(random.uniform(100, 1000), 1)
        optimal_speed = round(random.uniform(1000, 2000), 0)
        optimal_feed = round(random.uniform(200, 400), 0)
        confidence = round(random.uniform(0.8, 0.99), 2)

        try:
            await conn.execute(
                """
                INSERT INTO predictions (machine_id, timestamp, anomaly_score, failure_probability, remaining_useful_life, optimal_speed, optimal_feed, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id, timestamp) DO NOTHING;
            """,
                machine_id,
                current_time,
                anomaly_score,
                failure_probability,
                remaining_useful_life,
                optimal_speed,
                optimal_feed,
                confidence,
            )
            # print(f"Inserted prediction for {machine_id} at {current_time}")
        except Exception as e:
            print(f"Error inserting prediction for {machine_id} at {current_time}: {e}")

        current_time += timedelta(minutes=interval_minutes)


async def generate_alert_data(conn, machine_id, start_time, end_time):
    print(f"Generating alert data for {machine_id} from {start_time} to {end_time}...")
    current_time = start_time
    while current_time <= end_time:
        if random.random() < 0.1:  # 10% chance of an alert
            severity = random.choice(["low", "medium", "high"])
            alert_type = random.choice(
                [
                    "vibration_exceeded",
                    "temperature_spike",
                    "tool_wear_high",
                    "power_fluctuation",
                ]
            )
            message = f"Alert: {alert_type} detected on {machine_id} at {current_time.isoformat()}"
            acknowledged = random.choice([True, False])
            acknowledged_at = (
                current_time + timedelta(minutes=random.randint(5, 60))
                if acknowledged
                else None
            )
            acknowledged_by = (
                random.choice(["user1", "user2"]) if acknowledged else None
            )

            try:
                await conn.execute(
                    """
                    INSERT INTO alerts (machine_id, severity, type, message, timestamp, acknowledged, acknowledged_at, acknowledged_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    machine_id,
                    severity,
                    alert_type,
                    message,
                    current_time,
                    acknowledged,
                    acknowledged_at,
                    acknowledged_by,
                )
                print(f"Inserted alert for {machine_id} at {current_time}")
            except Exception as e:
                print(f"Error inserting alert for {machine_id} at {current_time}: {e}")

        current_time += timedelta(hours=1)


async def main():
    conn = None
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="cnc_password",
            database="cnc_intelligence",
        )
        await conn.set_type_codec(
            "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )
        print("Connected to PostgreSQL.")

        # Generate machine data
        await generate_machine_data(conn)

        # Generate prediction data for existing machines
        machine_ids = ["CNC-001", "CNC-002", "CNC-003"]
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)  # Last 7 days of data

        for mid in machine_ids:
            await generate_prediction_data(conn, mid, start_time, end_time)
            await generate_alert_data(conn, mid, start_time, end_time)

        print("Sample data generation complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            await conn.close()
            print("Disconnected from PostgreSQL.")


if __name__ == "__main__":
    asyncio.run(main())
