import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faTrash, faPlus, faSave, faTimes } from '@fortawesome/free-solid-svg-icons';
import { getApiUrl, SERVERS, ENDPOINTS } from '../config/api';

const RubricManagement = () => {
  const [rubrics, setRubrics] = useState([]);
  const [editingRubric, setEditingRubric] = useState(null);
  const [newRubric, setNewRubric] = useState({
    name: '',
    description: '',
    criteria: [{ description: '', weight: 0, levels: [{ score: 0, description: '' }] }]
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchRubrics();
  }, []);

  const fetchRubrics = async () => {
    try {
      const response = await fetch(getApiUrl(SERVERS.EVALUATION, ENDPOINTS.RUBRICS));
      if (!response.ok) throw new Error('Failed to fetch rubrics');
      const data = await response.json();
      setRubrics(data);
    } catch (err) {
      setError('Failed to load rubrics: ' + err.message);
    }
  };

  const handleSaveRubric = async (rubric) => {
    try {
      const url = rubric.id 
        ? `${getApiUrl(SERVERS.EVALUATION, ENDPOINTS.RUBRIC_EDIT)}/${rubric.id}`
        : getApiUrl(SERVERS.EVALUATION, ENDPOINTS.RUBRIC_EDIT);
      
      const response = await fetch(url, {
        method: rubric.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rubric)
      });

      if (!response.ok) throw new Error('Failed to save rubric');
      
      setSuccess('Rubric saved successfully!');
      fetchRubrics();
      setEditingRubric(null);
      setNewRubric({
        name: '',
        description: '',
        criteria: [{ description: '', weight: 0, levels: [{ score: 0, description: '' }] }]
      });
    } catch (err) {
      setError('Failed to save rubric: ' + err.message);
    }
  };

  const handleDeleteRubric = async (id) => {
    if (!window.confirm('Are you sure you want to delete this rubric?')) return;
    
    try {
      const response = await fetch(`${getApiUrl(SERVERS.EVALUATION, ENDPOINTS.RUBRIC_EDIT)}/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete rubric');
      
      setSuccess('Rubric deleted successfully!');
      fetchRubrics();
    } catch (err) {
      setError('Failed to delete rubric: ' + err.message);
    }
  };

  const addCriterion = (rubric) => {
    const updatedRubric = {
      ...rubric,
      criteria: [
        ...rubric.criteria,
        { description: '', weight: 0, levels: [{ score: 0, description: '' }] }
      ]
    };
    if (rubric === editingRubric) {
      setEditingRubric(updatedRubric);
    } else {
      setNewRubric(updatedRubric);
    }
  };

  const addLevel = (rubric, criterionIndex) => {
    const updatedCriteria = [...rubric.criteria];
    updatedCriteria[criterionIndex].levels.push({ score: 0, description: '' });
    
    const updatedRubric = { ...rubric, criteria: updatedCriteria };
    if (rubric === editingRubric) {
      setEditingRubric(updatedRubric);
    } else {
      setNewRubric(updatedRubric);
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 0' }}>
      <div className="text-center" style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', margin: 0 }}>Rubric Management</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Create and manage evaluation rubrics</p>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
          <button className="close" onClick={() => setError('')}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>
      )}

      {success && (
        <div className="alert alert-success" role="alert">
          {success}
          <button className="close" onClick={() => setSuccess('')}>
            <FontAwesomeIcon icon={faTimes} />
          </button>
        </div>
      )}

      {/* Create New Rubric Section */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3>Create New Rubric</h3>
        <div className="form-group">
          <input
            type="text"
            className="form-control"
            placeholder="Rubric Name"
            value={newRubric.name}
            onChange={(e) => setNewRubric({ ...newRubric, name: e.target.value })}
          />
        </div>
        <div className="form-group">
          <textarea
            className="form-control"
            placeholder="Description"
            value={newRubric.description}
            onChange={(e) => setNewRubric({ ...newRubric, description: e.target.value })}
          />
        </div>

        {/* Criteria */}
        {newRubric.criteria.map((criterion, cIndex) => (
          <div key={cIndex} className="card" style={{ margin: '1rem 0' }}>
            <div className="form-group">
              <input
                type="text"
                className="form-control"
                placeholder="Criterion Description"
                value={criterion.description}
                onChange={(e) => {
                  const updatedCriteria = [...newRubric.criteria];
                  updatedCriteria[cIndex].description = e.target.value;
                  setNewRubric({ ...newRubric, criteria: updatedCriteria });
                }}
              />
            </div>
            <div className="form-group">
              <input
                type="number"
                className="form-control"
                placeholder="Weight"
                value={criterion.weight}
                onChange={(e) => {
                  const updatedCriteria = [...newRubric.criteria];
                  updatedCriteria[cIndex].weight = parseFloat(e.target.value);
                  setNewRubric({ ...newRubric, criteria: updatedCriteria });
                }}
              />
            </div>

            {/* Levels */}
            {criterion.levels.map((level, lIndex) => (
              <div key={lIndex} className="level-group">
                <input
                  type="number"
                  className="form-control"
                  placeholder="Score"
                  value={level.score}
                  onChange={(e) => {
                    const updatedCriteria = [...newRubric.criteria];
                    updatedCriteria[cIndex].levels[lIndex].score = parseFloat(e.target.value);
                    setNewRubric({ ...newRubric, criteria: updatedCriteria });
                  }}
                />
                <input
                  type="text"
                  className="form-control"
                  placeholder="Level Description"
                  value={level.description}
                  onChange={(e) => {
                    const updatedCriteria = [...newRubric.criteria];
                    updatedCriteria[cIndex].levels[lIndex].description = e.target.value;
                    setNewRubric({ ...newRubric, criteria: updatedCriteria });
                  }}
                />
              </div>
            ))}
            <button
              className="btn btn-secondary"
              onClick={() => addLevel(newRubric, cIndex)}
            >
              Add Level
            </button>
          </div>
        ))}

        <div className="button-group">
          <button
            className="btn btn-secondary"
            onClick={() => addCriterion(newRubric)}
          >
            <FontAwesomeIcon icon={faPlus} /> Add Criterion
          </button>
          <button
            className="btn btn-primary"
            onClick={() => handleSaveRubric(newRubric)}
          >
            <FontAwesomeIcon icon={faSave} /> Save Rubric
          </button>
        </div>
      </div>

      {/* Existing Rubrics List */}
      <div className="card">
        <h3>Existing Rubrics</h3>
        <div className="rubrics-list">
          {rubrics.map((rubric) => (
            <div key={rubric.id} className="rubric-item">
              <div className="rubric-header">
                <h4>{rubric.name}</h4>
                <div className="actions">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setEditingRubric(rubric)}
                  >
                    <FontAwesomeIcon icon={faEdit} />
                  </button>
                  <button
                    className="btn btn-danger"
                    onClick={() => handleDeleteRubric(rubric.id)}
                  >
                    <FontAwesomeIcon icon={faTrash} />
                  </button>
                </div>
              </div>
              <p>{rubric.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RubricManagement;