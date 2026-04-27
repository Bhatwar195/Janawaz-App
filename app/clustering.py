import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session
from app.models import Complaint, Cluster


def run_clustering(db: Session):
    """
    Run DBSCAN clustering on all complaints, rebuild the clusters table.
    eps = 100 metres radius, min_samples = 2 complaints to form a cluster.
    """
    complaints = db.query(Complaint).all()
    if len(complaints) < 2:
        return

    coords = np.array([[c.latitude, c.longitude] for c in complaints])
    coords_rad = np.radians(coords)

    eps_rad = 0.1 / 6371.0  # 100 m in radians
    db_scan = DBSCAN(eps=eps_rad, min_samples=2, algorithm="ball_tree", metric="haversine")
    labels = db_scan.fit_predict(coords_rad)

    # Reset all cluster assignments
    for c in complaints:
        c.cluster_id = None
    db.query(Cluster).delete()
    db.commit()

    # Group by label
    groups: dict[int, list[Complaint]] = {}
    for complaint, label in zip(complaints, labels):
        if label >= 0:
            groups.setdefault(int(label), []).append(complaint)

    for group_complaints in groups.values():
        lats = [c.latitude for c in group_complaints]
        lngs = [c.longitude for c in group_complaints]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        total_upvotes = sum(c.upvote_count() for c in group_complaints)
        score = round(total_upvotes * 1.5 + len(group_complaints) * 2, 2)

        cluster = Cluster(
            center_lat=center_lat,
            center_lng=center_lng,
            score=score,
            complaint_count=len(group_complaints),
        )
        db.add(cluster)
        db.flush()

        for c in group_complaints:
            c.cluster_id = cluster.id

    db.commit()
