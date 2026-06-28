import pandas as pd


def generate_alerts(df: pd.DataFrame) -> list:
    """
    إنشاء التنبيهات الخاصة بإدارة الذمم.
    """

    alerts = []

    high_count = len(df[df["Age_90_Plus"] >= 1])

    medium_count = len(
        df[
            (df["Age_61_75"] >= 1)
            | (df["Age_76_90"] >= 1)
        ]
    )

    high_amount = df["Age_90_Plus"].sum()

    due_amount = df["DueBalance"].sum()

    if high_count > 0:
        alerts.append(
            f"🔴 يوجد {high_count:,} عميل لديهم ذمم أكثر من 90 يوم."
        )

    if medium_count > 0:
        alerts.append(
            f"🟠 يوجد {medium_count:,} عميل لديهم ذمم بين 61 و90 يوم."
        )

    if high_amount > 0:
        alerts.append(
            f"💰 إجمالي الذمم (+90) = {high_amount:,.3f}"
        )

    if due_amount > 0:
        alerts.append(
            f"📞 إجمالي الذمم المستحقة = {due_amount:,.3f}"
        )

    return alerts