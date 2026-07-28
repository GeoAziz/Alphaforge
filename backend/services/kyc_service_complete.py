"""
Enhanced KYCService with Onfido integration, AML screening, and enforcement.
Implements §11.1 Compliance Architecture.
"""

import logging
import httpx
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class KYCService:
    """
    KYC/AML verification service with Onfido integration.
    - Triggers KYC verification before live trading
    - Handles asynchronous webhooks from Onfido
    - Screens against OFAC/PEP lists
    - Blocks live trading for unverified users
    """

    ONFIDO_API_BASE = "https://api.onfido.com/v3.6"
    OFAC_CHECK_URL = "https://ofac-check-api.example.com/check"  # Stub - use real API

    def __init__(self, db, redis_client=None):
        self.db = db
        self.redis = redis_client
        self.onfido_api_key = os.getenv("ONFIDO_API_KEY", "")
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def initiate_kyc(
        self,
        user_id: str,
        email: str,
        full_name: str,
        date_of_birth: str,
        country: str
    ) -> Dict[str, Any]:
        """
        Initiate KYC verification process via Onfido.
        Returns SDK token for frontend KYC flow.
        """

        try:
            # 1. Create Onfido applicant
            applicant_response = await self._create_onfido_applicant(
                full_name, email, date_of_birth, country
            )

            if not applicant_response.get('success'):
                return {
                    'success': False,
                    'error': applicant_response.get('error', 'Applicant creation failed')
                }

            applicant_id = applicant_response.get('applicant_id')

            # 2. Create SDK token for frontend
            sdk_token_response = await self._create_sdk_token(applicant_id)

            if not sdk_token_response.get('success'):
                return {
                    'success': False,
                    'error': sdk_token_response.get('error', 'SDK token creation failed')
                }

            # 3. Store in database
            kyc_record = {
                'user_id': user_id,
                'status': 'SUBMITTED',
                'onfido_applicant_id': applicant_id,
                'aml_status': 'PENDING',
                'created_at': datetime.utcnow().isoformat()
            }

            self.db.supabase.table('kyc_verifications').upsert(kyc_record).execute()

            logger.info(f"✅ KYC initiated for {user_id}, applicant_id={applicant_id}")

            return {
                'success': True,
                'applicant_id': applicant_id,
                'sdk_token': sdk_token_response.get('sdk_token'),
                'status': 'INITIATED'
            }

        except Exception as e:
            logger.error(f"KYC initiation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _create_onfido_applicant(
        self,
        full_name: str,
        email: str,
        date_of_birth: str,
        country: str
    ) -> Dict[str, Any]:
        """Create applicant in Onfido."""

        try:
            url = f"{self.ONFIDO_API_BASE}/applicants"
            headers = {
                'Authorization': f'Token token={self.onfido_api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'first_name': full_name.split()[0],
                'last_name': ' '.join(full_name.split()[1:]),
                'email': email,
                'dob': date_of_birth,
                'country': country,
                'applicant_provides_data': True
            }

            response = await self.http_client.post(url, json=payload, headers=headers)

            if response.status_code != 201:
                logger.error(f"Onfido applicant creation failed: {response.text}")
                return {'success': False, 'error': response.text}

            data = response.json()
            return {
                'success': True,
                'applicant_id': data.get('id')
            }

        except Exception as e:
            logger.error(f"Applicant creation error: {e}")
            return {'success': False, 'error': str(e)}

    async def _create_sdk_token(self, applicant_id: str) -> Dict[str, Any]:
        """Create SDK token for Onfido web flow."""

        try:
            url = f"{self.ONFIDO_API_BASE}/sdk_token"
            headers = {
                'Authorization': f'Token token={self.onfido_api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'applicant_id': applicant_id,
                'referrer': 'https://alphaforge.app/*'
            }

            response = await self.http_client.post(url, json=payload, headers=headers)

            if response.status_code != 201:
                return {'success': False, 'error': response.text}

            data = response.json()
            return {
                'success': True,
                'sdk_token': data.get('token')
            }

        except Exception as e:
            logger.error(f"SDK token creation error: {e}")
            return {'success': False, 'error': str(e)}

    async def handle_verification_webhook(
        self,
        webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle async verification completion webhook from Onfido.
        Triggered when user submits ID + proof of address.
        """

        try:
            applicant_id = webhook_payload.get('object', {}).get('id')
            event_type = webhook_payload.get('action')

            # Fetch check results
            if event_type == 'check.completed':
                check_id = webhook_payload.get('object', {}).get('checks', [{}])[0].get('id')
                check_result = await self._fetch_check_result(applicant_id, check_id)

                # Update KYC status
                if check_result.get('result') == 'clear':
                    status = 'APPROVED'
                    aml_status = 'PENDING'  # Next: AML screening
                else:
                    status = 'REJECTED'
                    aml_status = 'FAILED'

                # Find user by applicant_id
                response = self.db.supabase.table('kyc_verifications').select('*').eq(
                    'onfido_applicant_id', applicant_id
                ).execute()

                if response.data:
                    user_id = response.data[0]['user_id']
                    self.db.supabase.table('kyc_verifications').update({
                        'status': status,
                        'onfido_check_id': check_id,
                        'aml_status': aml_status,
                        'completed_at': datetime.utcnow().isoformat(),
                        'verified_data': check_result
                    }).eq('user_id', user_id).execute()

                    logger.info(f"✅ KYC {status} for user {user_id}")

                    # Trigger AML screening if approved
                    if status == 'APPROVED':
                        await self.screen_ofac_pep(user_id)

            return {'success': True, 'status': status}

        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _fetch_check_result(
        self,
        applicant_id: str,
        check_id: str
    ) -> Dict[str, Any]:
        """Fetch check results from Onfido."""

        try:
            url = f"{self.ONFIDO_API_BASE}/applicants/{applicant_id}/checks/{check_id}"
            headers = {
                'Authorization': f'Token token={self.onfido_api_key}'
            }

            response = await self.http_client.get(url, headers=headers)

            if response.status_code != 200:
                return {'success': False, 'error': response.text}

            data = response.json()
            return {
                'success': True,
                'result': data.get('result'),
                'sub_result': data.get('sub_result'),
                'check_id': data.get('id')
            }

        except Exception as e:
            logger.error(f"Check result fetch failed: {e}")
            return {'success': False, 'error': str(e)}

    async def screen_ofac_pep(self, user_id: str) -> Dict[str, Any]:
        """
        Screen user against OFAC and PEP (Politically Exposed Person) lists.
        Blocks account if match found pending manual review.
        """

        try:
            # Fetch user details
            user_response = self.db.supabase.table('users').select('*').eq('id', user_id).execute()
            if not user_response.data:
                return {'success': False, 'error': 'User not found'}

            user = user_response.data[0]

            # Call OFAC/PEP API (stub implementation)
            screening_result = await self._call_ofac_api(
                user.get('display_name'),
                user.get('email')
            )

            if screening_result.get('match_found'):
                # Block account and file SAR
                self.db.supabase.table('kyc_verifications').update({
                    'aml_status': 'BLOCKED',
                    'aml_reason': f"SAR Match: {screening_result.get('match_reason')}"
                }).eq('user_id', user_id).execute()

                # Log for compliance team
                logger.warning(f"⚠️ AML BLOCK for {user_id}: {screening_result.get('match_reason')}")

                # File Suspicious Activity Report (stub)
                await self._file_sar(user_id, screening_result)

                return {
                    'success': False,
                    'blocked': True,
                    'reason': screening_result.get('match_reason')
                }
            else:
                # Approve
                self.db.supabase.table('kyc_verifications').update({
                    'aml_status': 'CLEAR',
                    'status': 'APPROVED'
                }).eq('user_id', user_id).execute()

                logger.info(f"✅ AML screening CLEAR for {user_id}")

                return {
                    'success': True,
                    'approved': True,
                    'aml_status': 'CLEAR'
                }

        except Exception as e:
            logger.error(f"AML screening failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _call_ofac_api(self, full_name: str, email: str) -> Dict[str, Any]:
        """Call OFAC/PEP screening API."""
        # Stub implementation - real API would screen against actual OFAC lists
        # Here we just simulate the check

        try:
            # In production, call real OFAC API
            suspicious_names = ['osama bin laden', 'kim jong', 'vladimir putin']  # Examples

            name_lower = full_name.lower()
            match_found = any(suspect in name_lower for suspect in suspicious_names)

            return {
                'match_found': match_found,
                'match_reason': f'Name match on OFAC list' if match_found else 'No match',
                'lists': ['OFAC_SDN', 'PEP_LIST'] if match_found else []
            }

        except Exception as e:
            logger.error(f"OFAC API call failed: {e}")
            return {'match_found': False, 'error': str(e)}

    async def _file_sar(self, user_id: str, screening_result: Dict[str, Any]):
        """File Suspicious Activity Report with FinCEN (stub)."""
        logger.warning(f"[STUB] Filing SAR for user {user_id}: {screening_result}")
        # In production, file actual SAR with FinCEN

    async def get_kyc_status(self, user_id: str) -> Dict[str, Any]:
        """Get KYC status for user."""

        try:
            response = self.db.supabase.table('kyc_verifications').select('*').eq(
                'user_id', user_id
            ).execute()

            if not response.data:
                return {
                    'status': 'NOT_STARTED',
                    'approved': False
                }

            kyc = response.data[0]
            return {
                'status': kyc.get('status'),
                'approved': kyc.get('status') == 'APPROVED',
                'aml_status': kyc.get('aml_status'),
                'completed_at': kyc.get('completed_at')
            }

        except Exception as e:
            logger.error(f"KYC status fetch failed: {e}")
            return {'status': 'ERROR', 'approved': False, 'error': str(e)}

    async def enforce_kyc_gate(self, user_id: str) -> Tuple[bool, str]:
        """
        Enforce KYC gate: block live trading if not approved.
        Returns (allowed: bool, reason: str)
        """

        kyc_status = await self.get_kyc_status(user_id)

        if not kyc_status.get('approved'):
            return False, f"Live trading requires KYC approval. Status: {kyc_status.get('status')}"

        return True, "KYC approved"
