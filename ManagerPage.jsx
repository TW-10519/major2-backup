import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function ManagerPage() {
  const [activeTab, setActiveTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [roles, setRoles] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [overtimes, setOvertimes] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [formData, setFormData] = useState({});
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchRoles();
  }, []);

  useEffect(() => {
    if (activeTab === 'employees') fetchEmployees();
    else if (activeTab === 'roles') fetchRoles();
    else if (activeTab === 'shifts') fetchShifts();
    else if (activeTab === 'schedules') fetchSchedules();
    else if (activeTab === 'attendance') fetchAttendance();
    else if (activeTab === 'overtime') fetchOvertimes();
    else if (activeTab === 'leaves') fetchLeaves();
  }, [activeTab]);

  const fetchRoles = async () => {
    try {
      const response = await api.get('/manager/roles');
      setRoles(response.data);
    } catch (error) {
      console.error('Failed to fetch roles');
    }
  };

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/employees');
      setEmployees(response.data);
    } catch (error) {
      alert('Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  };

  const fetchShifts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/shifts');
      setShifts(response.data);
    } catch (error) {
      alert('Failed to fetch shifts');
    } finally {
      setLoading(false);
    }
  };

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/schedules');
      setSchedules(response.data);
    } catch (error) {
      alert('Failed to fetch schedules');
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/attendance');
      setAttendance(response.data);
    } catch (error) {
      alert('Failed to fetch attendance');
    } finally {
      setLoading(false);
    }
  };

  const fetchOvertimes = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/overtime');
      setOvertimes(response.data);
    } catch (error) {
      alert('Failed to fetch overtime');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const response = await api.get('/manager/leaves');
      setLeaves(response.data);
    } catch (error) {
      alert('Failed to fetch leaves');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  const openModal = (type, data = {}) => {
    setModalType(type);
    setFormData(data);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setFormData({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalType === 'create-employee') {
        await api.post('/manager/employees', formData);
        fetchEmployees();
      } else if (modalType === 'create-role') {
        // Convert work_days string to array
        const payload = { ...formData, work_days: formData.work_days.split(',').map(d => d.trim()) };
        await api.post('/manager/roles', payload);
        fetchRoles();
      } else if (modalType === 'create-shift') {
        await api.post('/manager/shifts', formData);
        fetchShifts();
      } else if (modalType === 'create-schedule') {
        await api.post('/manager/schedules', formData);
        fetchSchedules();
      } else if (modalType === 'generate-schedule') {
        const response = await api.post('/manager/schedules/generate', formData);
        alert(`Generated ${response.data.created} schedules`);
        fetchSchedules();
      }
      closeModal();
    } catch (error) {
      alert(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleApproval = async (type, id, status) => {
    try {
      if (type === 'overtime') {
        await api.put(`/manager/overtime/${id}/approve`, { approval_status: status });
        fetchOvertimes();
      } else if (type === 'leave') {
        await api.put(`/manager/leaves/${id}/approve`, { approval_status: status });
        fetchLeaves();
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Approval failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Manager Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">Welcome, {user.name}</span>
            <button
              onClick={handleLogout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="border-b border-gray-200 mb-6 overflow-x-auto">
          <nav className="flex space-x-8">
            {['employees', 'roles', 'shifts', 'schedules', 'attendance', 'overtime', 'leaves'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        {/* Employees Tab */}
        {activeTab === 'employees' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Employees</h2>
              <button
                onClick={() => openModal('create-employee')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Add Employee
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {employees.map((emp) => (
                    <tr key={emp.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{emp.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{emp.username}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{emp.role_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${emp.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {emp.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Roles</h2>
              <button
                onClick={() => openModal('create-role')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Add Role
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {roles.map((role) => (
                <div key={role.id} className="bg-white shadow rounded-lg p-4">
                  <h3 className="font-semibold text-lg mb-2">{role.name}</h3>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>Type: {role.employment_type || 'N/A'}</p>
                    <p>Work Days: {role.work_days?.join(', ')}</p>
                    <p>Daily Hours: {role.daily_work_hours || 'N/A'}</p>
                    <p>Weekly Limit: {role.weekly_hours_limit || 'N/A'}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Shifts Tab */}
        {activeTab === 'shifts' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Shifts</h2>
              <button
                onClick={() => openModal('create-shift')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Add Shift
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Day</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {shifts.map((shift) => (
                    <tr key={shift.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{shift.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{shift.role_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{shift.day_of_week}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{shift.start_time} - {shift.end_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Schedules Tab */}
        {activeTab === 'schedules' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Schedules</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => openModal('create-schedule')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                >
                  Add Schedule
                </button>
                <button
                  onClick={() => openModal('generate-schedule')}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
                >
                  Generate Schedules
                </button>
              </div>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shift</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {schedules.slice(0, 50).map((schedule) => (
                    <tr key={schedule.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.employee_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.shift_name || 'Custom'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.start_time} - {schedule.end_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Attendance Tab */}
        {activeTab === 'attendance' && (
          <div>
            <h2 className="text-xl font-semibold mb-6">Attendance Records</h2>
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clock In</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clock Out</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hours</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {attendance.slice(0, 50).map((att) => (
                    <tr key={att.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{att.employee_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.clock_in || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.clock_out || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.worked_hours?.toFixed(2) || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${att.status === 'PRESENT' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {att.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Overtime Tab */}
        {activeTab === 'overtime' && (
          <div>
            <h2 className="text-xl font-semibold mb-6">Overtime Requests</h2>
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hours</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {overtimes.map((ot) => (
                    <tr key={ot.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.employee_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.actual_hours}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.overtime_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          ot.approval_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          ot.approval_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {ot.approval_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {ot.approval_status === 'PENDING' && (
                          <>
                            <button
                              onClick={() => handleApproval('overtime', ot.id, 'APPROVED')}
                              className="text-green-600 hover:text-green-900 mr-3"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleApproval('overtime', ot.id, 'REJECTED')}
                              className="text-red-600 hover:text-red-900"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Leaves Tab */}
        {activeTab === 'leaves' && (
          <div>
            <h2 className="text-xl font-semibold mb-6">Leave Requests</h2>
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Employee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaves.map((leave) => (
                    <tr key={leave.id}>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.employee_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.leave_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.duration}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          leave.approval_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          leave.approval_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {leave.approval_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {leave.approval_status === 'PENDING' && (
                          <>
                            <button
                              onClick={() => handleApproval('leave', leave.id, 'APPROVED')}
                              className="text-green-600 hover:text-green-900 mr-3"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleApproval('leave', leave.id, 'REJECTED')}
                              className="text-red-600 hover:text-red-900"
                            >
                              Reject
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              {modalType.replace('-', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Employee Form */}
              {modalType === 'create-employee' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Username</label>
                    <input
                      type="text"
                      value={formData.username || ''}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Password</label>
                    <input
                      type="password"
                      value={formData.password || ''}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Role</label>
                    <select
                      value={formData.role_id || ''}
                      onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Role</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              {/* Role Form */}
              {modalType === 'create-role' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Work Days (comma-separated: Mon,Tue,Wed)</label>
                    <input
                      type="text"
                      value={formData.work_days || ''}
                      onChange={(e) => setFormData({ ...formData, work_days: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="Mon,Tue,Wed,Thu,Fri"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Break Minutes</label>
                    <input
                      type="number"
                      value={formData.break_minutes || ''}
                      onChange={(e) => setFormData({ ...formData, break_minutes: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Employment Type</label>
                    <select
                      value={formData.employment_type || ''}
                      onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="">Select Type</option>
                      <option value="FULL_TIME">Full Time</option>
                      <option value="PART_TIME">Part Time</option>
                    </select>
                  </div>
                </>
              )}

              {/* Shift Form */}
              {modalType === 'create-shift' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Name</label>
                    <input
                      type="text"
                      value={formData.name || ''}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Role</label>
                    <select
                      value={formData.role_id || ''}
                      onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Role</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Day of Week (1=Mon, 7=Sun)</label>
                    <input
                      type="number"
                      min="1"
                      max="7"
                      value={formData.day_of_week || ''}
                      onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Start Time (HH:MM)</label>
                    <input
                      type="text"
                      value={formData.start_time || ''}
                      onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="09:00"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">End Time (HH:MM)</label>
                    <input
                      type="text"
                      value={formData.end_time || ''}
                      onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="17:00"
                      required
                    />
                  </div>
                </>
              )}

              {/* Schedule Form */}
              {modalType === 'create-schedule' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Employee</label>
                    <select
                      value={formData.employee_id || ''}
                      onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Employee</option>
                      {employees.map((emp) => (
                        <option key={emp.id} value={emp.id}>{emp.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Shift (optional)</label>
                    <select
                      value={formData.shift_id || ''}
                      onChange={(e) => setFormData({ ...formData, shift_id: e.target.value || null })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="">Custom Shift</option>
                      {shifts.map((shift) => (
                        <option key={shift.id} value={shift.id}>{shift.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Date</label>
                    <input
                      type="date"
                      value={formData.date || ''}
                      onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Start Time (HH:MM)</label>
                    <input
                      type="text"
                      value={formData.start_time || ''}
                      onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="09:00"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">End Time (HH:MM)</label>
                    <input
                      type="text"
                      value={formData.end_time || ''}
                      onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      placeholder="17:00"
                      required
                    />
                  </div>
                </>
              )}

              {/* Generate Schedule Form */}
              {modalType === 'generate-schedule' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Role</label>
                    <select
                      value={formData.role_id || ''}
                      onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Role</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>{role.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Start Date</label>
                    <input
                      type="date"
                      value={formData.start_date || ''}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">End Date</label>
                    <input
                      type="date"
                      value={formData.end_date || ''}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                </>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 py-2 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
