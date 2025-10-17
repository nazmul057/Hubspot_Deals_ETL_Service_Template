import dlt
import logging
from typing import Dict, List, Any, Iterator, Optional, Callable
from datetime import datetime, timezone
from .api_service import APIService
from loki_logger import get_logger, log_business_event, log_security_event
from .api_service import APIService
from .hubspot_api_service import HubSpotAPIService

# --- HubSpot helpers (dates & numbers) ---
from typing import Any, Optional, Dict, List
from datetime import datetime, timezone

STANDARD_PROPERTIES: List[str] = [
    "dealname","amount","dealstage","pipeline","closedate","createdate",
    "hs_lastmodifieddate","hubspot_owner_id","dealtype","description",
    "hs_deal_stage_probability","hs_analytics_source","hs_analytics_source_data_1",
    "hs_analytics_source_data_2","archived",
]

def _to_timestamp(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            ms = int(value)
            return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat()
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None

def _to_decimal(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except Exception:
        return None

def create_data_source(
    job_config: Dict[str, Any],
    auth_config: Dict[str, Any],
    filters: Dict[str, Any],
    checkpoint_callback: Optional[Callable] = None,
    check_cancel_callback: Optional[Callable] = None,
    check_pause_callback: Optional[Callable] = None,  # Add pause callback parameter
    resume_from: Optional[Dict[str, Any]] = None,
):
    """
    Create DLT source function for Hubspot_Deals data extraction with checkpoint support
    """
    logger = get_logger(__name__)
    api_service = APIService(base_url="https://api.hubapi.com" , test_delay_seconds=1)

    # This was set up to test the hubspot url with a custom file
    # svc = HubSpotAPIService(base_url="https://api.hubapi.com")

    access_token = auth_config.get("accessToken")
    if not access_token:
        raise ValueError("No access token found in auth configuration")

    organization_id = job_config.get("organizationId")
    if not organization_id:
        raise ValueError("No organization ID found in job configuration")

    #  To Be Removed Later
    logger.info(
        "Starting Hubspot_Deals data extraction",
        extra={
            "organization_id": organization_id,
            "filters": filters,
            "auth_config": auth_config,
            "job_config": job_config,
        },
    )

    @dlt.resource(name="hubspot_deals", write_disposition="replace", primary_key="hubspot_deal_id")
    def get_main_data() -> Iterator[Dict[str, Any]]:
        """
        Extract main data from Hubspot_Deals API with checkpoint support

        TODO: Customize for Hubspot_Deals:
        - Update resource name and primary_key
        - Adjust API calls and pagination
        - Modify data transformation logic
        """

        # Initialize state
        if resume_from:
            after = resume_from.get("cursor")
            page_count = resume_from.get("page_number", 0)
            total_records = resume_from.get("records_processed", 0)
            logger.info(
                "Resuming data extraction",
                extra={
                    "operation": "data_extraction",
                    "page_number": page_count + 1,
                    "total_processed": total_records,
                },
            )
        else:
            after = None
            page_count = 0
            total_records = 0
            logger.info(
                "Starting fresh data extraction",
                extra={"operation": "data_extraction", "source": "hubspot_deals"},
            )

        # Configuration
        checkpoint_interval = 10
        cancel_check_interval = 1
        pause_check_interval = 1  # Check for pause more frequently than cancel
        job_id = filters.get("scan_id", "unknown")

        # page_size = int(filters.get("pageSize", 100))  # HubSpot max 100
        # properties = filters.get("properties") or STANDARD_PROPERTIES

        while page_count < 1000:  # Safety limit
            try:
                # Check for cancellation
                if page_count % cancel_check_interval == 0:
                    if check_cancel_callback and check_cancel_callback(job_id):
                        logger.info(
                            "Extraction cancelled by user",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save cancellation checkpoint
                        if checkpoint_callback:
                            try:
                                cancel_checkpoint = {
                                    "phase": "main_data_cancelled",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": 100,
                                    "checkpoint_data": {
                                        "cancellation_reason": "user_requested",
                                        "cancelled_at_page": page_count,
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(job_id, cancel_checkpoint)
                            except Exception as e:
                                logger.warning(
                                    "Failed to save cancellation checkpoint",
                                    extra={"job_id": job_id, "error": str(e)},
                                )
                        break

                # Check for pause request
                if page_count % pause_check_interval == 0:
                    if check_pause_callback and check_pause_callback(job_id):
                        logger.info(
                            "Extraction paused by user",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save pause checkpoint - this allows resuming from exact position
                        if checkpoint_callback:
                            try:
                                pause_checkpoint = {
                                    "phase": "main_data_paused",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": 1,
                                    "checkpoint_data": {
                                        "pause_reason": "user_requested",
                                        "paused_at_page": page_count,
                                        "paused_at": datetime.now(
                                            timezone.utc
                                        ).isoformat(),
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(job_id, pause_checkpoint)

                                logger.info(
                                    "Pause checkpoint saved",
                                    extra={
                                        "operation": "data_extraction",
                                        "job_id": job_id,
                                        "page_number": page_count,
                                        "total_processed": total_records,
                                    },
                                )
                            except Exception as e:
                                logger.warning(
                                    "Failed to save pause checkpoint",
                                    extra={"job_id": job_id, "error": str(e)},
                                )

                        # Exit gracefully - this allows the job to be resumed later
                        break

                logger.debug(
                    "Fetching data page",
                    extra={
                        "operation": "data_extraction",
                        "job_id": job_id,
                        "page_number": page_count + 1,
                    },
                )

                
                # TODO: Replace with appropriate Hubspot_Deals API call
                data = api_service.get_data(
                    access_token=access_token, limit=20, after=after,
                )
                
                # HubSpot CRM v3 deals (cursor pagination via `after`)
                '''
                data = svc._request(
                    "GET",
                    "/crm/v3/objects/deals",
                    params={
                    "limit": page_size,
                    "after": after,
                    "properties": ",".join(properties),
                    "archived": "false",
                    },
                )
                '''
                '''
                # svc = HubSpotAPIService()
                data = svc.get_deals(
                    access_token=access_token,
                    # limit=page_size,
                    limit=20,
                    after=after,
                    url="/crm/v3/objects/deals")
                '''

                page_records = 0

                # TODO: Update data processing based on Hubspot_Deals response structure
                data_key = "results"  # Update based on API response
                if data_key in data and data[data_key]:
                    for record in data[data_key]:
                        # Check for pause/cancel even within record processing for faster response
                        if check_pause_callback and check_pause_callback(job_id):
                            logger.info(
                                "Extraction paused mid-page",
                                extra={
                                    "operation": "data_extraction",
                                    "job_id": job_id,
                                    "page_number": page_count + 1,
                                    "records_in_page": page_records,
                                    "total_processed": total_records + page_records,
                                },
                            )

                            # Save mid-page pause checkpoint
                            if checkpoint_callback:
                                try:
                                    mid_page_checkpoint = {
                                        "phase": "main_data_paused_mid_page",
                                        "records_processed": total_records
                                        + page_records,
                                        "cursor": after,
                                        "page_number": page_count,
                                        "batch_size": 100,
                                        "checkpoint_data": {
                                            "pause_reason": "user_requested_mid_page",
                                            "paused_at_page": page_count,
                                            "records_completed_in_page": page_records,
                                            "paused_at": datetime.now(
                                                timezone.utc
                                            ).isoformat(),
                                            "service": "hubspot_deals",
                                        },
                                    }
                                    checkpoint_callback(job_id, mid_page_checkpoint)
                                except Exception as e:
                                    logger.warning(
                                        "Failed to save mid-page pause checkpoint",
                                        extra={"job_id": job_id, "error": str(e)},
                                    )
                            return  # Exit the generator

                        # Filter properties if specified
                        if "properties" in filters and filters["properties"]:
                            filtered_record = {
                                prop: record.get(prop)
                                for prop in filters["properties"]
                                if prop in record
                            }
                            filtered_record["id"] = record.get("id")  # Always keep ID
                        else:
                            properties = record.get("properties") or {}

                            # Map and convert known fields
                            out: Dict[str, Any] = {
                                "hubspot_deal_id": record.get("id"),
                                "dealname": properties.get("dealname"),
                                "amount": _to_decimal(properties.get("amount")),
                                "dealstage": properties.get("dealstage"),
                                "pipeline": properties.get("pipeline"),
                                "closedate": _to_timestamp(properties.get("closedate")),
                                "createdate": _to_timestamp(properties.get("createdate")),
                                "hs_lastmodifieddate": _to_timestamp(properties.get("hs_lastmodifieddate")),
                                "hs_object_id": properties.get("hs_object_id"),
                                # "hubspot_owner_id": properties.get("hubspot_owner_id"),
                                # "dealtype": properties.get("dealtype"),
                                # "description": properties.get("description"),
                                # "hs_deal_stage_probability": _to_decimal(properties.get("hs_deal_stage_probability")),
                                # "hs_analytics_source": properties.get("hs_analytics_source"),
                                # "hs_analytics_source_data_1": properties.get("hs_analytics_source_data_1"),
                                # "hs_analytics_source_data_2": properties.get("hs_analytics_source_data_2"),
                                "archived": bool(record.get("archived", False)),
                                # JSONB buckets
                                # "raw_properties": properties,
                                # "custom_properties": _extract_custom_properties(properties),
                                # Associations not fetched here; can be added with another call if needed
                                # "associations": item.get("associations"),
                                # Multi-tenant & ETL metadata
                                # "tenant_id": tenant_id,
                                # "_tenant_id": tenant_id,
                                # "_scan_id": scan_id,
                                # "_extracted_at": datetime.now(timezone.utc).isoformat(),
                                # "_page_number": page + 1,
                            }
                            filtered_record = out

                        # Add extraction metadata
                        filtered_record.update(
                            {
                                "_extracted_at": datetime.now(timezone.utc).isoformat(),
                                "_scan_id": filters.get("scan_id", "unknown"),
                                "_organization_id": filters.get(
                                    "organization_id", "unknown"
                                ),
                                "_tenant_id": filters.get(
                                    "organization_id", "unknown"
                                ),
                                "_page_number": page_count + 1,
                                "_source_service": "hubspot_deals",
                            }
                        )

                        yield filtered_record
                        page_records += 1

                # Update counters
                total_records += page_records
                page_count += 1

                # Save checkpoint periodically
                if checkpoint_callback and page_count % checkpoint_interval == 0:
                    try:
                        # TODO: Update pagination logic based on Hubspot_Deals API
                        next_cursor = None
                        if (
                            data.get("paging")
                            and data["paging"].get("next")
                            and data["paging"]["next"].get("after")
                        ):
                            next_cursor = data["paging"]["next"]["after"]

                        checkpoint_data = {
                            "phase": "main_data",
                            "records_processed": total_records,
                            "cursor": next_cursor,
                            "page_number": page_count,
                            "batch_size": 100,
                            "checkpoint_data": {
                                "pages_processed": page_count,
                                "last_page_records": page_records,
                                "service": "hubspot_deals",
                            },
                        }

                        checkpoint_callback(job_id, checkpoint_data)

                        logger.debug(
                            "Checkpoint saved",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count,
                                "total_records": total_records,
                            },
                        )

                    except Exception as checkpoint_error:
                        logger.warning(
                            "Failed to save checkpoint",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "error": str(checkpoint_error),
                            },
                        )

                # TODO: Handle pagination based on Hubspot_Deals API response
                if (
                    data.get("paging")
                    and data["paging"].get("next")
                    and data["paging"]["next"].get("after")
                ):
                    after = data["paging"]["next"]["after"]
                elif data.get("has_more"):
                    after = data.get("next_cursor")
                elif data.get("next_page_token"):
                    after = data.get("next_page_token")
                else:
                    # Final checkpoint on completion
                    if checkpoint_callback:
                        try:
                            final_checkpoint = {
                                "phase": "main_data_completed",
                                "records_processed": total_records,
                                "cursor": None,
                                "page_number": page_count,
                                "batch_size": 100,
                                "checkpoint_data": {
                                    "completion_status": "success",
                                    "total_pages": page_count,
                                    "final_total": total_records,
                                    "service": "hubspot_deals",
                                },
                            }
                            checkpoint_callback(job_id, final_checkpoint)
                        except Exception as e:
                            logger.warning(
                                "Failed to save final checkpoint",
                                extra={"job_id": job_id, "error": str(e)},
                            )

                    logger.info(
                        "Data extraction completed",
                        extra={
                            "operation": "data_extraction",
                            "job_id": job_id,
                            "total_records": total_records,
                            "total_pages": page_count,
                        },
                    )
                    break

            except Exception as e:
                logger.error(
                    "Error fetching data page",
                    extra={
                        "operation": "data_extraction",
                        "job_id": job_id,
                        "page_number": page_count + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Save error checkpoint for debugging
                if checkpoint_callback:
                    try:
                        error_checkpoint = {
                            "phase": "main_data_error",
                            "records_processed": total_records,
                            "cursor": after,
                            "page_number": page_count,
                            "batch_size": 100,
                            "checkpoint_data": {
                                "error": str(e),
                                "error_page": page_count + 1,
                                "recovery_cursor": after,
                                "service": "hubspot_deals",
                            },
                        }
                        checkpoint_callback(job_id, error_checkpoint)
                    except:
                        pass

                raise e

    return [get_main_data]