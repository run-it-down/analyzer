import pickle


def classify_murderous_duo(p1_kp, p2_kp, p1_kda, p2_kda):
    model = pickle.load(open('./kmeans_murderous.pkl', 'rb'))
    centres = model.cluster_centers_.tolist()
    prediction = model.predict([[p1_kp, p1_kda], [p2_kp, p2_kda]])

    return {
        "cluster_centre": {
            "0": centres[0],
            "1": centres[1]
        },
        "1": {
            "isClass": not bool(prediction[0]),
            "value": [p1_kp, p1_kda]
        },
        "2": {
            "isClass": not bool(prediction[1]),
            "value": [p2_kp, p2_kp]
        }
    }
