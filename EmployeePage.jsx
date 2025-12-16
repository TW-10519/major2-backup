import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function EmployeePage() {
  const [activeTab, setActiveTab] = useState('schedules');
  const [schedules, setSchedules] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [overtime, setOvertime] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [formData, setFormData] = useState({});
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (activeTab === 'schedules') fetchSchedules();
    else if (activeTab === 'attendance') fetchAttendance();
    else if (activeTab === 'overtime') fetchOvertime();
    else if (activeTab === 'leaves') fetchLeaves();
  }, [activeTab]);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/employee/profile');
      setProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch profile');
    }
  };

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employee/schedules');
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
      const response = await api.get('/employee/attendance');
      setAttendance(response.data);
    } catch (error) {
      alert('Failed to fetch attendance');
    } finally {
      setLoading(false);
    }
  };

  const fetchOvertime = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employee/overtime');
      setOvertime(response.data);
    } catch (error) {
      alert('Failed to fetch overtime');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employee/leaves');
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

  const handleClockIn = async (date) => {
    try {
      await api.post('/employee/clock-in', {
        employee_id: user.user_id,
        date: date
      });
      alert('Clocked in successfully');
      fetchAttendance();
    } catch (error) {
      alert(error.response?.data?.detail || 'Clock in failed');
    }
  };

  const handleClockOut = async (date) => {
    try {
      const response = await api.post('/employee/clock-out', {
        employee_id: user.user_id,
        date: date
      });
      alert(`Clocked out successfully. Worked ${response.data.worked_hours.toFixed(2)} hours`);
      fetchAttendance();
    } catch (error) {
      alert(error.response?.data?.detail || 'Clock out failed');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (modalType === 'request-leave') {
        await api.post('/employee/leaves', {
          ...formData,
          employee_id: user.user_id
        });
        alert('Leave request submitted');
        fetchLeaves();
      } else if (modalType === 'request-overtime') {
        await api.post('/employee/overtime', {
          ...formData,
          employee_id: user.user_id
        });
        alert('Overtime request submitted');
        fetchOvertime();
      }
      closeModal();
    } catch (error) {
      alert(error.response?.data?.detail || 'Request failed');
    }
  };

  const getTodaySchedule = () => {
    const today = new Date().toISOString().split('T')[0];
    return schedules.find(s => s.date === today);
  };

  const todaySchedule = getTodaySchedule();
  const todayAttendance = attendance.find(a => a.date === new Date().toISOString().split('T')[0]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Employee Portal</h1>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Profile Card */}
        {profile && (
          <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Profile</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-500">Department</p>
                <p className="font-semibold">{profile.department_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Role</p>
                <p className="font-semibold">{profile.role_name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Leave Balance</p>
                <p className="font-semibold">
                  {(profile.yearly_paid_leave_allowance || 0) - (profile.yearly_paid_leave_used || 0)} days
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Overtime Used</p>
                <p className="font-semibold">{profile.monthly_overtime_used?.toFixed(2) || 0} hrs</p>
              </div>
            </div>
          </div>
        )}

        {/* Today's Schedule & Clock In/Out */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Today's Schedule</h2>
          {todaySchedule ? (
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div className="mb-4 md:mb-0">
                <p className="text-lg">
                  <span className="font-semibold">{todaySchedule.shift_name}</span>
                </p>
                <p className="text-gray-600">
                  {todaySchedule.start_time} - {todaySchedule.end_time}
                </p>
                {todayAttendance && (
                  <div className="mt-2 space-y-1">
                    {todayAttendance.clock_in && (
                      <p className="text-sm text-green-600">
                        ✓ Clocked in at {todayAttendance.clock_in}
                      </p>
                    )}
                    {todayAttendance.clock_out && (
                      <p className="text-sm text-green-600">
                        ✓ Clocked out at {todayAttendance.clock_out} ({todayAttendance.worked_hours?.toFixed(2)} hours)
                      </p>
                    )}
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                {!todayAttendance?.clock_in && (
                  <button
                    onClick={() => handleClockIn(new Date().toISOString().split('T')[0])}
                    className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg"
                  >
                    Clock In
                  </button>
                )}
                {todayAttendance?.clock_in && !todayAttendance?.clock_out && (
                  <button
                    onClick={() => handleClockOut(new Date().toISOString().split('T')[0])}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
                  >
                    Clock Out
                  </button>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No schedule for today</p>
          )}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8">
            {['schedules', 'attendance', 'overtime', 'leaves'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
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

        {/* Schedules Tab */}
        {activeTab === 'schedules' && (
          <div>
            <h2 className="text-xl font-semibold mb-6">My Schedules</h2>
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Shift</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Overtime</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {schedules.map((schedule, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{schedule.shift_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {schedule.start_time} - {schedule.end_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {schedule.overtime_hours > 0 ? `${schedule.overtime_hours} hrs` : '-'}
                      </td>
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
            <h2 className="text-xl font-semibold mb-6">Attendance History</h2>
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clock In</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Clock Out</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Worked Hours</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {attendance.map((att, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">{att.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.clock_in || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{att.clock_out || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {att.worked_hours ? `${att.worked_hours.toFixed(2)} hrs` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          att.status === 'PRESENT' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
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
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Overtime Records</h2>
              <button
                onClick={() => openModal('request-overtime')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Request Overtime
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hours</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Compensation</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {overtime.map((ot, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.actual_hours}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.overtime_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{ot.compensation_mode}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          ot.approval_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          ot.approval_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {ot.approval_status}
                        </span>
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
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Leave Records</h2>
              <button
                onClick={() => openModal('request-leave')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Request Leave
              </button>
            </div>

            <div className="bg-white shadow rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaves.map((leave, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.date}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.leave_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{leave.duration}</td>
                      <td className="px-6 py-4">{leave.reason || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          leave.approval_status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                          leave.approval_status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {leave.approval_status}
                        </span>
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
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {modalType === 'request-leave' ? 'Request Leave' : 'Request Overtime'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
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

              {modalType === 'request-leave' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Leave Type</label>
                    <select
                      value={formData.leave_type || ''}
                      onChange={(e) => setFormData({ ...formData, leave_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Type</option>
                      <option value="PAID">Paid Leave</option>
                      <option value="UNPAID">Unpaid Leave</option>
                      <option value="COMP_OFF">Compensatory Off</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Duration</label>
                    <select
                      value={formData.duration || ''}
                      onChange={(e) => setFormData({ ...formData, duration: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Duration</option>
                      <option value="FULL_DAY">Full Day</option>
                      <option value="HALF_DAY">Half Day</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reason</label>
                    <textarea
                      value={formData.reason || ''}
                      onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      rows="3"
                    />
                  </div>
                </>
              )}

              {modalType === 'request-overtime' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Hours</label>
                    <input
                      type="number"
                      step="0.5"
                      value={formData.actual_hours || ''}
                      onChange={(e) => setFormData({ ...formData, actual_hours: parseFloat(e.target.value) })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Overtime Type</label>
                    <select
                      value={formData.overtime_type || ''}
                      onChange={(e) => setFormData({ ...formData, overtime_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Type</option>
                      <option value="NORMAL">Normal</option>
                      <option value="NIGHT">Night</option>
                      <option value="HOLIDAY">Holiday</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Compensation Mode</label>
                    <select
                      value={formData.compensation_mode || ''}
                      onChange={(e) => setFormData({ ...formData, compensation_mode: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                      required
                    >
                      <option value="">Select Mode</option>
                      <option value="EXTRA_PAY">Extra Pay</option>
                      <option value="COMP_OFF">Compensatory Off</option>
                    </select>
                  </div>
                </>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
                >
                  Submit
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
