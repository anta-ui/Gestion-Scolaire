# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import random
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AIOptimizer(models.Model):
    _name = 'edu.ai.optimizer'
    _description = 'Optimiseur IA pour emplois du temps'

    name = fields.Char(
        string='Nom de l\'optimisation',
        required=True
    )
    
    timetable_id = fields.Many2one(
        'edu.timetable.enhanced',
        string='Emploi du temps',
        required=True
    )
    
    optimization_type = fields.Selection([
        ('genetic', 'Algorithme génétique'),
        ('simulated_annealing', 'Recuit simulé'),
        ('local_search', 'Recherche locale'),
        ('constraint_satisfaction', 'Satisfaction de contraintes'),
        ('hybrid', 'Hybride'),
    ], string='Type d\'optimisation', default='genetic', required=True)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échec'),
    ], string='État', default='draft')
    
    # Paramètres d'optimisation
    population_size = fields.Integer(
        string='Taille de population',
        default=50,
        help='Nombre d\'individus dans la population (algorithme génétique)'
    )
    
    max_generations = fields.Integer(
        string='Générations maximum',
        default=100,
        help='Nombre maximum de générations'
    )
    
    mutation_rate = fields.Float(
        string='Taux de mutation',
        default=0.1,
        help='Probabilité de mutation (0.0 - 1.0)'
    )
    
    crossover_rate = fields.Float(
        string='Taux de croisement',
        default=0.8,
        help='Probabilité de croisement (0.0 - 1.0)'
    )
    
    elite_size = fields.Integer(
        string='Taille de l\'élite',
        default=5,
        help='Nombre d\'individus élites conservés'
    )
    
    # Résultats
    start_time = fields.Datetime(
        string='Début d\'optimisation',
        readonly=True
    )
    
    end_time = fields.Datetime(
        string='Fin d\'optimisation',
        readonly=True
    )
    
    duration = fields.Float(
        string='Durée (secondes)',
        compute='_compute_duration'
    )
    
    initial_score = fields.Float(
        string='Score initial',
        readonly=True
    )
    
    final_score = fields.Float(
        string='Score final',
        readonly=True
    )
    
    improvement = fields.Float(
        string='Amélioration (%)',
        compute='_compute_improvement'
    )
    
    generations_completed = fields.Integer(
        string='Générations complétées',
        readonly=True
    )
    
    best_solution = fields.Text(
        string='Meilleure solution (JSON)',
        readonly=True
    )
    
    optimization_log = fields.Text(
        string='Journal d\'optimisation',
        readonly=True
    )
    
    # Statistiques
    constraint_violations = fields.Integer(
        string='Violations de contraintes',
        readonly=True
    )
    
    hard_violations = fields.Integer(
        string='Violations dures',
        readonly=True
    )
    
    soft_violations = fields.Integer(
        string='Violations souples',
        readonly=True
    )
    
    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds()
            else:
                record.duration = 0.0
    
    @api.depends('initial_score', 'final_score')
    def _compute_improvement(self):
        for record in self:
            if record.initial_score and record.initial_score > 0:
                record.improvement = ((record.final_score - record.initial_score) / record.initial_score) * 100
            else:
                record.improvement = 0.0
    
    def optimize_timetable(self, timetable):
        """Méthode principale d'optimisation"""
        self.ensure_one()
        
        try:
            self.write({
                'state': 'running',
                'start_time': fields.Datetime.now(),
                'timetable_id': timetable.id,
            })
            
            # Évaluation initiale
            initial_score = self._evaluate_timetable(timetable)
            self.initial_score = initial_score
            
            # Sélection de l'algorithme
            if self.optimization_type == 'genetic':
                final_score, best_solution = self._genetic_algorithm(timetable)
            elif self.optimization_type == 'simulated_annealing':
                final_score, best_solution = self._simulated_annealing(timetable)
            elif self.optimization_type == 'local_search':
                final_score, best_solution = self._local_search(timetable)
            elif self.optimization_type == 'constraint_satisfaction':
                final_score, best_solution = self._constraint_satisfaction(timetable)
            else:  # hybrid
                final_score, best_solution = self._hybrid_optimization(timetable)
            
            # Appliquer la meilleure solution
            self._apply_solution(timetable, best_solution)
            
            # Finaliser l'optimisation
            self.write({
                'state': 'completed',
                'end_time': fields.Datetime.now(),
                'final_score': final_score,
                'best_solution': json.dumps(best_solution),
            })
            
            # Mettre à jour le score du timetable
            timetable.write({
                'optimization_score': final_score,
                'last_optimization': fields.Datetime.now(),
            })
            
            _logger.info(f'Optimisation terminée pour {timetable.name}: {initial_score:.2f} -> {final_score:.2f}')
            
        except Exception as e:
            self.write({
                'state': 'failed',
                'end_time': fields.Datetime.now(),
                'optimization_log': str(e),
            })
            _logger.error(f'Erreur lors de l\'optimisation: {e}')
            raise UserError(_('Erreur lors de l\'optimisation: %s') % str(e))
    
    def _genetic_algorithm(self, timetable):
        """Algorithme génétique pour l'optimisation"""
        _logger.info('Début de l\'algorithme génétique')
        
        # Initialiser la population
        population = self._initialize_population(timetable)
        best_score = 0
        best_solution = None
        generation = 0
        
        for generation in range(self.max_generations):
            # Évaluer la population
            scored_population = []
            for individual in population:
                score = self._evaluate_individual(timetable, individual)
                scored_population.append((score, individual))
            
            # Trier par score (descendant)
            scored_population.sort(key=lambda x: x[0], reverse=True)
            
            # Mettre à jour le meilleur
            if scored_population[0][0] > best_score:
                best_score = scored_population[0][0]
                best_solution = scored_population[0][1].copy()
            
            # Critère d'arrêt
            if best_score >= 95.0:  # Score suffisamment bon
                break
            
            # Sélection des parents (élitisme + sélection par tournoi)
            parents = self._select_parents(scored_population)
            
            # Nouvelle génération
            new_population = []
            
            # Conserver l'élite
            for i in range(min(self.elite_size, len(parents))):
                new_population.append(parents[i][1].copy())
            
            # Croisement et mutation
            while len(new_population) < self.population_size:
                if random.random() < self.crossover_rate and len(parents) >= 2:
                    parent1 = random.choice(parents)[1]
                    parent2 = random.choice(parents)[1]
                    child = self._crossover(parent1, parent2)
                else:
                    child = random.choice(parents)[1].copy()
                
                if random.random() < self.mutation_rate:
                    child = self._mutate(timetable, child)
                
                new_population.append(child)
            
            population = new_population
        
        self.generations_completed = generation + 1
        _logger.info(f'Algorithme génétique terminé après {generation + 1} générations')
        
        return best_score, best_solution
    
    def _simulated_annealing(self, timetable):
        """Algorithme de recuit simulé"""
        _logger.info('Début du recuit simulé')
        
        # Solution initiale
        current_solution = self._generate_random_solution(timetable)
        current_score = self._evaluate_individual(timetable, current_solution)
        
        best_solution = current_solution.copy()
        best_score = current_score
        
        # Paramètres du recuit
        initial_temp = 1000.0
        final_temp = 1.0
        cooling_rate = 0.95
        temperature = initial_temp
        
        iteration = 0
        max_iterations = 1000
        
        while temperature > final_temp and iteration < max_iterations:
            # Générer une solution voisine
            neighbor = self._generate_neighbor(timetable, current_solution)
            neighbor_score = self._evaluate_individual(timetable, neighbor)
            
            # Décider d'accepter ou non
            if neighbor_score > current_score or random.random() < self._acceptance_probability(current_score, neighbor_score, temperature):
                current_solution = neighbor
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_solution = current_solution.copy()
                    best_score = current_score
            
            temperature *= cooling_rate
            iteration += 1
        
        _logger.info(f'Recuit simulé terminé après {iteration} itérations')
        return best_score, best_solution
    
    def _local_search(self, timetable):
        """Recherche locale simple"""
        _logger.info('Début de la recherche locale')
        
        current_solution = self._generate_random_solution(timetable)
        current_score = self._evaluate_individual(timetable, current_solution)
        
        improved = True
        iteration = 0
        max_iterations = 500
        
        while improved and iteration < max_iterations:
            improved = False
            
            # Générer tous les voisins possibles
            neighbors = self._generate_all_neighbors(timetable, current_solution)
            
            for neighbor in neighbors:
                neighbor_score = self._evaluate_individual(timetable, neighbor)
                
                if neighbor_score > current_score:
                    current_solution = neighbor
                    current_score = neighbor_score
                    improved = True
                    break
            
            iteration += 1
        
        _logger.info(f'Recherche locale terminée après {iteration} itérations')
        return current_score, current_solution
    
    def _constraint_satisfaction(self, timetable):
        """Algorithme de satisfaction de contraintes"""
        _logger.info('Début de la satisfaction de contraintes')
        
        # Implémenter CSP basique
        # Pour l'instant, utiliser la recherche locale
        return self._local_search(timetable)
    
    def _hybrid_optimization(self, timetable):
        """Optimisation hybride combinant plusieurs méthodes"""
        _logger.info('Début de l\'optimisation hybride')
        
        # Phase 1: Algorithme génétique rapide
        self.max_generations = 50
        genetic_score, genetic_solution = self._genetic_algorithm(timetable)
        
        # Phase 2: Amélioration par recherche locale
        self.best_solution = json.dumps(genetic_solution)
        local_score, local_solution = self._local_search_from_solution(timetable, genetic_solution)
        
        # Phase 3: Affinage par recuit simulé
        final_score, final_solution = self._simulated_annealing_from_solution(timetable, local_solution)
        
        _logger.info('Optimisation hybride terminée')
        return final_score, final_solution
    
    def _initialize_population(self, timetable):
        """Initialiser la population pour l'algorithme génétique"""
        population = []
        
        for _ in range(self.population_size):
            individual = self._generate_random_solution(timetable)
            population.append(individual)
        
        return population
    
    def _generate_random_solution(self, timetable):
        """Générer une solution aléatoire"""
        solution = {}
        
        # Récupérer tous les créneaux
        slots = timetable.schedule_line_ids
        
        # Récupérer les ressources disponibles
        teachers = self.env['op.faculty'].search([('active', '=', True)])
        rooms = self.env['edu.room.enhanced'].search([('active', '=', True)])
        subjects = self.env['op.subject'].search([('active', '=', True)])
        classes = self.env['op.batch'].search([('active', '=', True)])
        
        for slot in slots:
            solution[slot.id] = {
                'teacher_id': random.choice(teachers).id if teachers else False,
                'room_id': random.choice(rooms).id if rooms else False,
                'subject_id': random.choice(subjects).id if subjects else False,
                'class_id': random.choice(classes).id if classes else False,
            }
        
        return solution
    
    def _evaluate_timetable(self, timetable):
        """Évaluer la qualité globale d'un emploi du temps"""
        score = 100.0  # Score de base
        
    def _evaluate_timetable(self, timetable):
        """Évaluer la qualité globale d'un emploi du temps"""
        score = 100.0  # Score de base
        
        # Pénalités pour les violations de contraintes
        constraints = timetable.constraint_ids.filtered(lambda x: x.active)
        
        for constraint in constraints:
            violations = constraint._check_constraint_violations()
            violation_count = len(violations)
            
            if violation_count > 0:
                if constraint.constraint_type == 'hard':
                    score -= violation_count * 10  # Pénalité forte
                elif constraint.constraint_type == 'soft':
                    score -= violation_count * 5   # Pénalité moyenne
                else:  # preference
                    score -= violation_count * 2   # Pénalité faible
        
        # Bonus pour l'équilibrage
        score += self._calculate_balance_bonus(timetable)
        
        # Bonus pour l'utilisation optimale des ressources
        score += self._calculate_resource_utilization_bonus(timetable)
        
        return max(0, score)  # Score minimum de 0
    
    def _evaluate_individual(self, timetable, solution):
        """Évaluer un individu (solution) spécifique"""
        # Appliquer temporairement la solution pour l'évaluation
        original_data = {}
        
        for slot_id, assignment in solution.items():
            slot = self.env['edu.schedule.slot'].browse(slot_id)
            if slot.exists():
                original_data[slot_id] = {
                    'teacher_id': slot.teacher_id.id,
                    'room_id': slot.room_id.id,
                    'subject_id': slot.subject_id.id,
                    'class_id': slot.class_id.id,
                }
                
                # Appliquer temporairement
                slot.write(assignment)
        
        # Évaluer
        score = self._evaluate_timetable(timetable)
        
        # Restaurer les données originales
        for slot_id, original_assignment in original_data.items():
            slot = self.env['edu.schedule.slot'].browse(slot_id)
            if slot.exists():
                slot.write(original_assignment)
        
        return score
    
    def _calculate_balance_bonus(self, timetable):
        """Calculer le bonus d'équilibrage"""
        bonus = 0.0
        
        # Équilibrage par jour
        slots_by_day = {}
        for slot in timetable.schedule_line_ids.filtered(lambda x: x.subject_id):
            day = slot.day_of_week
            if day not in slots_by_day:
                slots_by_day[day] = 0
            slots_by_day[day] += 1
        
        if slots_by_day:
            avg_slots = sum(slots_by_day.values()) / len(slots_by_day)
            variance = sum((count - avg_slots) ** 2 for count in slots_by_day.values()) / len(slots_by_day)
            
            # Moins de variance = meilleur équilibrage
            bonus += max(0, 10 - variance)
        
        return bonus
    
    def _calculate_resource_utilization_bonus(self, timetable):
        """Calculer le bonus d'utilisation des ressources"""
        bonus = 0.0
        
        # Utilisation des salles
        filled_slots = timetable.schedule_line_ids.filtered(lambda x: x.subject_id)
        total_slots = timetable.schedule_line_ids
        
        if total_slots:
            utilization_rate = len(filled_slots) / len(total_slots)
            bonus += utilization_rate * 10  # Bonus basé sur le taux d'utilisation
        
        return bonus
    
    def _select_parents(self, scored_population):
        """Sélectionner les parents pour la reproduction"""
        # Sélection par tournoi
        tournament_size = 3
        parents = []
        
        for _ in range(len(scored_population) // 2):
            tournament = random.sample(scored_population, min(tournament_size, len(scored_population)))
            winner = max(tournament, key=lambda x: x[0])
            parents.append(winner)
        
        return parents
    
    def _crossover(self, parent1, parent2):
        """Croisement entre deux parents"""
        child = {}
        
        for slot_id in parent1.keys():
            if random.random() < 0.5:
                child[slot_id] = parent1[slot_id].copy()
            else:
                child[slot_id] = parent2[slot_id].copy()
        
        return child
    
    def _mutate(self, timetable, individual):
        """Mutation d'un individu"""
        mutated = individual.copy()
        
        # Sélectionner aléatoirement quelques créneaux à muter
        slots_to_mutate = random.sample(list(individual.keys()), 
                                      max(1, int(len(individual) * self.mutation_rate)))
        
        # Ressources disponibles
        teachers = self.env['op.faculty'].search([('active', '=', True)])
        rooms = self.env['edu.room.enhanced'].search([('active', '=', True)])
        subjects = self.env['op.subject'].search([('active', '=', True)])
        classes = self.env['op.batch'].search([('active', '=', True)])
        
        for slot_id in slots_to_mutate:
            assignment = mutated[slot_id]
            
            # Muter aléatoirement un aspect
            mutation_type = random.choice(['teacher', 'room', 'subject', 'class'])
            
            if mutation_type == 'teacher' and teachers:
                assignment['teacher_id'] = random.choice(teachers).id
            elif mutation_type == 'room' and rooms:
                assignment['room_id'] = random.choice(rooms).id
            elif mutation_type == 'subject' and subjects:
                assignment['subject_id'] = random.choice(subjects).id
            elif mutation_type == 'class' and classes:
                assignment['class_id'] = random.choice(classes).id
        
        return mutated
    
    def _generate_neighbor(self, timetable, solution):
        """Générer une solution voisine"""
        neighbor = solution.copy()
        
        # Choisir aléatoirement un créneau à modifier
        slot_id = random.choice(list(solution.keys()))
        
        # Ressources disponibles
        teachers = self.env['op.faculty'].search([('active', '=', True)])
        rooms = self.env['edu.room.enhanced'].search([('active', '=', True)])
        subjects = self.env['op.subject'].search([('active', '=', True)])
        classes = self.env['op.batch'].search([('active', '=', True)])
        
        # Modifier aléatoirement un aspect
        mutation_type = random.choice(['teacher', 'room', 'subject', 'class'])
        
        if mutation_type == 'teacher' and teachers:
            neighbor[slot_id]['teacher_id'] = random.choice(teachers).id
        elif mutation_type == 'room' and rooms:
            neighbor[slot_id]['room_id'] = random.choice(rooms).id
        elif mutation_type == 'subject' and subjects:
            neighbor[slot_id]['subject_id'] = random.choice(subjects).id
        elif mutation_type == 'class' and classes:
            neighbor[slot_id]['class_id'] = random.choice(classes).id
        
        return neighbor
    
    def _generate_all_neighbors(self, timetable, solution):
        """Générer tous les voisins possibles (version simplifiée)"""
        neighbors = []
        
        # Pour la recherche locale, générer seulement un échantillon de voisins
        for _ in range(min(20, len(solution))):
            neighbor = self._generate_neighbor(timetable, solution)
            neighbors.append(neighbor)
        
        return neighbors
    
    def _acceptance_probability(self, current_score, neighbor_score, temperature):
        """Calculer la probabilité d'acceptation pour le recuit simulé"""
        if neighbor_score > current_score:
            return 1.0
        else:
            import math
            try:
                return math.exp((neighbor_score - current_score) / temperature)
            except OverflowError:
                return 0.0
    
    def _local_search_from_solution(self, timetable, initial_solution):
        """Recherche locale à partir d'une solution donnée"""
        current_solution = initial_solution.copy()
        current_score = self._evaluate_individual(timetable, current_solution)
        
        improved = True
        iteration = 0
        max_iterations = 100  # Réduit pour la phase hybride
        
        while improved and iteration < max_iterations:
            improved = False
            
            neighbors = self._generate_all_neighbors(timetable, current_solution)
            
            for neighbor in neighbors:
                neighbor_score = self._evaluate_individual(timetable, neighbor)
                
                if neighbor_score > current_score:
                    current_solution = neighbor
                    current_score = neighbor_score
                    improved = True
                    break
            
            iteration += 1
        
        return current_score, current_solution
    
    def _simulated_annealing_from_solution(self, timetable, initial_solution):
        """Recuit simulé à partir d'une solution donnée"""
        current_solution = initial_solution.copy()
        current_score = self._evaluate_individual(timetable, current_solution)
        
        best_solution = current_solution.copy()
        best_score = current_score
        
        initial_temp = 100.0  # Température réduite pour l'affinage
        final_temp = 1.0
        cooling_rate = 0.95
        temperature = initial_temp
        
        iteration = 0
        max_iterations = 200  # Réduit pour la phase hybride
        
        while temperature > final_temp and iteration < max_iterations:
            neighbor = self._generate_neighbor(timetable, current_solution)
            neighbor_score = self._evaluate_individual(timetable, neighbor)
            
            if neighbor_score > current_score or random.random() < self._acceptance_probability(current_score, neighbor_score, temperature):
                current_solution = neighbor
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_solution = current_solution.copy()
                    best_score = current_score
            
            temperature *= cooling_rate
            iteration += 1
        
        return best_score, best_solution
    
    def _apply_solution(self, timetable, solution):
        """Appliquer la solution optimale au timetable"""
        if not solution:
            return
        
        for slot_id, assignment in solution.items():
            slot = self.env['edu.schedule.slot'].browse(slot_id)
            if slot.exists():
                try:
                    slot.write(assignment)
                except Exception as e:
                    _logger.warning(f'Impossible d\'appliquer l\'assignation pour le créneau {slot_id}: {e}')
    
    def action_start_optimization(self):
        """Démarrer l'optimisation manuellement"""
        self.ensure_one()
        
        if not self.timetable_id:
            raise UserError(_('Veuillez spécifier un emploi du temps.'))
        
        if self.state == 'running':
            raise UserError(_('Une optimisation est déjà en cours.'))
        
        # Lancer l'optimisation en arrière-plan
        self.optimize_timetable(self.timetable_id)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Optimisation démarrée'),
                'message': _('L\'optimisation de l\'emploi du temps a été lancée.'),
                'type': 'success',
            }
        }
    
    def action_view_results(self):
        """Voir les résultats de l'optimisation"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Résultats d\'optimisation'),
            'res_model': 'edu.ai.optimizer',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def auto_optimize_all_timetables(self):
        """Optimiser automatiquement tous les emplois du temps actifs"""
        timetables = self.env['edu.timetable.enhanced'].search([
            ('state', 'in', ['generated', 'optimized']),
            ('ai_enabled', '=', True),
        ])
        
        optimized_count = 0
        
        for timetable in timetables:
            try:
                optimizer = self.create({
                    'name': f'Auto-optimisation {timetable.name}',
                    'timetable_id': timetable.id,
                    'optimization_type': timetable.ai_optimization_level,
                })
                
                optimizer.optimize_timetable(timetable)
                optimized_count += 1
                
            except Exception as e:
                _logger.error(f'Erreur lors de l\'auto-optimisation de {timetable.name}: {e}')
        
        _logger.info(f'Auto-optimisation terminée: {optimized_count} emplois du temps optimisés')
        
        return optimized_count
