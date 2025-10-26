from football_api_v3 import APIFootballV3

api = APIFootballV3("6336fb21e17dea87880d3b133132a13f")
result = api.get_predictions(1035021)  # Test fixture

print('Status:', result.status.value)
if result.data:
    print('Data found:', len(result.data))
    prediction = result.data[0] if result.data else None
    if prediction:
        predictions = prediction.get('predictions', {})
        print('Predictions structure:', type(predictions))
        print('Predictions keys:', list(predictions.keys()) if isinstance(predictions, dict) else 'Not a dict')
        
        percent = predictions.get('percent', {}) if isinstance(predictions, dict) else {}
        print('Percent data:', percent)
        
        if percent:
            print('Home percent:', percent.get('home'))
            print('Draw percent:', percent.get('draw'))
            print('Away percent:', percent.get('away'))
else:
    print('No data')