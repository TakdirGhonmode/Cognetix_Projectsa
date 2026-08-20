from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from database import get_db
from models import Ticket, TicketHistory, User
from schemas import TicketCreate, TicketUpdate, TicketResponse, TicketHistoryResponse
from auth import get_current_user, admin_required

router = APIRouter(prefix="/tickets", tags=["Tickets"])

VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]

VALID_STATUSES = [
    "Open",
    "In Progress",
    "Resolved",
    "Closed",
    "Reopened"
]

VALID_TRANSITIONS = {
    "Open": ["In Progress"],
    "In Progress": ["Resolved"],
    "Resolved": ["Closed"],
    "Closed": ["Reopened"],
    "Reopened": ["In Progress"]
}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if ticket.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid priority"
        )

    new_ticket = Ticket(
        customer_name=ticket.customer_name,
        issue_description=ticket.issue_description,
        category=ticket.category,
        priority=ticket.priority,
        status="Open",
        created_by=current_user.id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    history = TicketHistory(
        ticket_id=new_ticket.id,
        action="Ticket Created",
        old_value=None,
        new_value="Open",
        performed_by=current_user.id
    )

    db.add(history)
    db.commit()

    return {
        "status": "success",
        "message": "Ticket created successfully",
        "data": {
            "ticket_id": new_ticket.id,
            "customer_name": new_ticket.customer_name,
            "issue_description": new_ticket.issue_description,
            "category": new_ticket.category,
            "priority": new_ticket.priority,
            "status": new_ticket.status,
            "created_by": new_ticket.created_by
        }
    }


@router.get("/")
def get_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Ticket)

    # User role-based access control: standard users can only view their own tickets
    if current_user.role != "Admin":
        query = query.filter(Ticket.created_by == current_user.id)

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status}"
            )
        query = query.filter(Ticket.status == status)

    if priority:
        if priority not in VALID_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid priority filter: {priority}"
            )
        query = query.filter(Ticket.priority == priority)

    if date:
        query = query.filter(func.date(Ticket.created_date) == date)

    tickets = query.all()

    return {
        "status": "success",
        "message": "Tickets retrieved successfully",
        "data": [
            {
                "id": t.id,
                "customer_name": t.customer_name,
                "issue_description": t.issue_description,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "created_date": t.created_date.isoformat() if t.created_date else None,
                "updated_date": t.updated_date.isoformat() if t.updated_date else None,
                "created_by": t.created_by,
                "assigned_to": t.assigned_to
            }
            for t in tickets
        ]
    }


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if current_user.role != "Admin" and ticket.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this ticket"
        )

    return {
        "status": "success",
        "message": "Ticket retrieved successfully",
        "data": {
            "id": ticket.id,
            "customer_name": ticket.customer_name,
            "issue_description": ticket.issue_description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_date": ticket.created_date.isoformat() if ticket.created_date else None,
            "updated_date": ticket.updated_date.isoformat() if ticket.updated_date else None,
            "created_by": ticket.created_by,
            "assigned_to": ticket.assigned_to
        }
    }


@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Update description
    if update.issue_description is not None and update.issue_description != ticket.issue_description:
        old_value = ticket.issue_description
        ticket.issue_description = update.issue_description

        db.add(TicketHistory(
            ticket_id=ticket.id,
            action="Issue Description Updated",
            old_value=old_value,
            new_value=update.issue_description,
            performed_by=current_user.id
        ))

    # Update priority
    if update.priority is not None and update.priority != ticket.priority:
        if update.priority not in VALID_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority"
            )

        old_value = ticket.priority
        ticket.priority = update.priority

        db.add(TicketHistory(
            ticket_id=ticket.id,
            action="Priority Changed",
            old_value=old_value,
            new_value=update.priority,
            performed_by=current_user.id
        ))

    # Update status & transition validation
    if update.status is not None and update.status != ticket.status:
        if update.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status"
            )

        allowed = VALID_TRANSITIONS.get(ticket.status, [])

        if update.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: {ticket.status} -> {update.status}"
            )

        old_value = ticket.status
        ticket.status = update.status

        db.add(TicketHistory(
            ticket_id=ticket.id,
            action=f"Status Changed ({update.status})",
            old_value=old_value,
            new_value=update.status,
            performed_by=current_user.id
        ))

    # Assign ticket
    if update.assigned_to is not None and update.assigned_to != ticket.assigned_to:
        # Verify assigned user exists
        assigned_user = db.query(User).filter(User.id == update.assigned_to).first()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user not found"
            )

        old_value = str(ticket.assigned_to) if ticket.assigned_to else "Unassigned"
        ticket.assigned_to = update.assigned_to

        db.add(TicketHistory(
            ticket_id=ticket.id,
            action="Ticket Assigned",
            old_value=old_value,
            new_value=str(update.assigned_to),
            performed_by=current_user.id
        ))

    db.commit()
    db.refresh(ticket)

    return {
        "status": "success",
        "message": "Ticket updated successfully",
        "data": {
            "id": ticket.id,
            "customer_name": ticket.customer_name,
            "issue_description": ticket.issue_description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "created_date": ticket.created_date.isoformat() if ticket.created_date else None,
            "updated_date": ticket.updated_date.isoformat() if ticket.updated_date else None,
            "created_by": ticket.created_by,
            "assigned_to": ticket.assigned_to
        }
    }


@router.get("/{ticket_id}/history")
def get_ticket_history(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    if current_user.role != "Admin" and ticket.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this ticket's history"
        )

    history_records = db.query(TicketHistory).filter(
        TicketHistory.ticket_id == ticket_id
    ).order_by(TicketHistory.timestamp.asc()).all()

    return {
        "status": "success",
        "message": "Ticket history retrieved successfully",
        "data": [
            {
                "id": h.id,
                "ticket_id": h.ticket_id,
                "action": h.action,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "performed_by": h.performed_by,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None
            }
            for h in history_records
        ]
    }