from copy import deepcopy

from django.utils import timezone

from edge_api.identities.tasks import (
    call_environment_webhook_for_feature_state_change,
    sync_identity_document_features,
)
from environments.models import Webhook
from webhooks.webhooks import WebhookEventType


def test_call_environment_webhook_for_feature_state_change_with_new_state_only(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    new_enabled_state = True
    new_value = "foo"

    # When
    call_environment_webhook_for_feature_state_change(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        new_enabled_state=new_enabled_state,
        new_value=new_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED

    mock_generate_webhook_feature_state_data.assert_called_once_with(
        feature,
        environment,
        identity.id,
        identity.identifier,
        new_enabled_state,
        new_value,
    )
    data = call_args[0][1]
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_with_previous_state_only(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    previous_enabled_state = True
    previous_value = "foo"

    # When
    call_environment_webhook_for_feature_state_change(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        previous_enabled_state=previous_enabled_state,
        previous_value=previous_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_DELETED

    mock_generate_webhook_feature_state_data.assert_called_once_with(
        feature,
        environment,
        identity.id,
        identity.identifier,
        previous_enabled_state,
        previous_value,
    )
    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_with_both_states(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(environment=environment, url="https://foo.com/webhook")

    mock_feature_state_data = mocker.MagicMock()
    mock_generate_webhook_feature_state_data = mocker.patch.object(
        Webhook,
        "generate_webhook_feature_state_data",
        return_value=mock_feature_state_data,
    )

    now_isoformat = timezone.now().isoformat()
    previous_enabled_state = False
    previous_value = "foo"

    new_enabled_state = True
    new_value = "bar"

    # When
    call_environment_webhook_for_feature_state_change(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        previous_enabled_state=previous_enabled_state,
        previous_value=previous_value,
        new_enabled_state=new_enabled_state,
        new_value=new_value,
    )

    # Then
    mock_call_environment_webhooks.assert_called_once()
    call_args = mock_call_environment_webhooks.call_args

    assert call_args[0][0] == environment
    assert call_args[1]["event_type"] == WebhookEventType.FLAG_UPDATED

    assert mock_generate_webhook_feature_state_data.call_count == 2
    mock_generate_data_calls = mock_generate_webhook_feature_state_data.call_args_list

    assert mock_generate_data_calls[0][0] == (
        feature,
        environment,
        identity.id,
        identity.identifier,
        previous_enabled_state,
        previous_value,
    )

    assert mock_generate_data_calls[1][0] == (
        feature,
        environment,
        identity.id,
        identity.identifier,
        new_enabled_state,
        new_value,
    )

    data = call_args[0][1]
    assert data["previous_state"] == mock_feature_state_data
    assert data["new_state"] == mock_feature_state_data
    assert data["changed_by"] == admin_user.email
    assert data["timestamp"] == now_isoformat


def test_call_environment_webhook_for_feature_state_change_does_nothing_if_no_webhooks(
    mocker, environment, feature, identity, admin_user
):
    # Given
    mock_call_environment_webhooks = mocker.patch(
        "edge_api.identities.tasks.call_environment_webhooks"
    )
    Webhook.objects.create(
        environment=environment, url="https://foo.com/webhook", enabled=False
    )
    now_isoformat = timezone.now().isoformat()

    # When
    call_environment_webhook_for_feature_state_change(
        feature_id=feature.id,
        environment_api_key=environment.api_key,
        identity_id=identity.id,
        identity_identifier=identity.identifier,
        changed_by_user_id=admin_user.id,
        timestamp=now_isoformat,
        new_enabled_state=True,
        new_value="foo",
    )

    # Then
    mock_call_environment_webhooks.assert_not_called()


def test_sync_identity_document_features_removes_deleted_features(
    mocker, identity_document_without_fs, environment, feature
):
    # Given
    dynamo_wrapper_mock = mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper"
    )

    identity_document = deepcopy(identity_document_without_fs)
    identity_uuid = identity_document["identity_uuid"]

    # let's add a feature to the identity that is not in the environment
    identity_document["identity_features"].append(
        {
            "feature_state_value": "feature_1_value",
            "featurestate_uuid": "4a8fbe06-d4cd-4686-a184-d924844bb422",
            "django_id": 1,
            "feature": {
                "name": "feature_that_does_not_exists",
                "type": "STANDARD",
                "id": 99,
            },
            "enabled": True,
        }
    )
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document_without_fs

    # When
    sync_identity_document_features(identity_uuid)

    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(identity_uuid)
    dynamo_wrapper_mock.put_item.assert_called_with(identity_document_without_fs)
