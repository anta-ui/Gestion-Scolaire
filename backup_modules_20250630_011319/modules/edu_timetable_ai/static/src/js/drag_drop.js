/** @odoo-module **/

/**
 * Gestionnaire du glisser-déposer pour l'emploi du temps
 */
export class DragDropManager {
    constructor(container) {
        this.container = container;
        this.isDragging = false;
        this.dragData = null;
        
        this.initEventListeners();
    }

    /**
     * Initialiser les écouteurs d'événements
     */
    initEventListeners() {
        this.container.addEventListener('dragstart', this.onDragStart.bind(this));
        this.container.addEventListener('dragover', this.onDragOver.bind(this));
        this.container.addEventListener('drop', this.onDrop.bind(this));
        this.container.addEventListener('dragend', this.onDragEnd.bind(this));
    }

    /**
     * Début du drag
     */
    onDragStart(event) {
        this.isDragging = true;
        this.dragData = {
            element: event.target,
            startPosition: {
                x: event.clientX,
                y: event.clientY
            }
        };
        
        event.target.classList.add('dragging');
        console.log('Début du glisser-déposer');
    }

    /**
     * Survol lors du drag
     */
    onDragOver(event) {
        event.preventDefault();
        if (this.isDragging) {
            // Logique de survol à implémenter
        }
    }

    /**
     * Dépot de l'élément
     */
    onDrop(event) {
        event.preventDefault();
        if (this.isDragging && this.dragData) {
            // Logique de dépôt à implémenter
            console.log('Élément déposé');
            this.updateTimetable(event);
        }
    }

    /**
     * Fin du drag
     */
    onDragEnd(event) {
        this.isDragging = false;
        if (this.dragData) {
            this.dragData.element.classList.remove('dragging');
            this.dragData = null;
        }
        console.log('Fin du glisser-déposer');
    }

    /**
     * Mettre à jour l'emploi du temps
     */
    updateTimetable(event) {
        // Logique de mise à jour à implémenter
        console.log('Mise à jour de l\'emploi du temps');
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function() {
    const timetableContainer = document.querySelector('.timetable-container');
    if (timetableContainer) {
        new DragDropManager(timetableContainer);
    }
});
