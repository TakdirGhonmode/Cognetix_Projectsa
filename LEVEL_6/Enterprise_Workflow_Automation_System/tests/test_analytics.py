from services.analytics_service import calculate_completion_rates, calculate_bottlenecks, calculate_approval_times

def test_analytics_metrics(db_session):
    completion_data = calculate_completion_rates(db_session)
    assert hasattr(completion_data, "completion_rate_percent")
    
    bottleneck_data = calculate_bottlenecks(db_session)
    assert hasattr(bottleneck_data, "total_bottlenecks")

    approval_data = calculate_approval_times(db_session)
    assert hasattr(approval_data, "overall_avg_hours")
